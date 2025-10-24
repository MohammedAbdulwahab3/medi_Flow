"""
Communication center views for unified messaging and notifications
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone

from prescription.models import Message, Notification
from prescription.communication_utils import send_message, get_contactable_users
from authentication_app.models import User


@login_required
def communication_center(request):
    """Unified communication center showing messages and notifications"""
    user = request.user
    
    # Get unread counts
    unread_messages = Message.objects.filter(recipient=user, is_read=False).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    # Get recent messages (conversations)
    received_messages = Message.objects.filter(
        recipient=user
    ).select_related('sender').order_by('-sent_at')[:10]
    
    sent_messages = Message.objects.filter(
        sender=user
    ).select_related('recipient').order_by('-sent_at')[:10]
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')[:15]
    
    # Get contactable users
    contacts = get_contactable_users(user)
    
    context = {
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications,
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'recent_notifications': recent_notifications,
        'contacts': contacts,
    }
    
    return render(request, 'frontend/communication/center.html', context)


@login_required
def quick_message(request):
    """Quick message sending (AJAX endpoint)"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        subject = request.POST.get('subject', 'Quick Message')
        body = request.POST.get('body')
        
        if not recipient_id or not body:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        try:
            recipient = User.objects.get(id=recipient_id)
            message = send_message(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body
            )
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'message': 'Message sent successfully'
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Recipient not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


@login_required
def conversation_view(request, user_id):
    """View conversation with a specific user"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Get all messages between these two users
    messages_qs = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).select_related('sender', 'recipient').order_by('sent_at')
    
    # Mark received messages as read
    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    # Handle new message in conversation
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            message = send_message(
                sender=request.user,
                recipient=other_user,
                subject=f'Conversation with {other_user.full_name or other_user.username}',
                body=body
            )
            django_messages.success(request, 'Message sent')
            return redirect('frontend:conversation_view', user_id=user_id)
    
    context = {
        'other_user': other_user,
        'messages': messages_qs,
    }
    
    return render(request, 'frontend/communication/conversation.html', context)


@login_required
def search_users(request):
    """Search users for messaging (AJAX endpoint)"""
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')  # Optional role filter
    
    if not query or len(query) < 2:
        return JsonResponse({'users': []})
    
    # Get contactable users first
    contacts = get_contactable_users(request.user)
    
    # Combine all contactable users
    contactable_ids = []
    for user_list in contacts.values():
        contactable_ids.extend([u.id for u in user_list])
    
    # Search within contactable users
    users = User.objects.filter(
        id__in=contactable_ids
    ).filter(
        Q(username__icontains=query) |
        Q(full_name__icontains=query) |
        Q(email__icontains=query)
    )
    
    if role:
        users = users.filter(role=role)
    
    users = users[:10]
    
    results = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'role': user.get_role_display(),
    } for user in users]
    
    return JsonResponse({'users': results})


@login_required
def notification_center(request):
    """View all notifications with filtering"""
    notification_type = request.GET.get('type', '')
    read_status = request.GET.get('status', 'all')  # all, read, unread
    
    notifications = Notification.objects.filter(user=request.user)
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if read_status == 'read':
        notifications = notifications.filter(is_read=True)
    elif read_status == 'unread':
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')
    
    # Get available notification types for filter
    available_types = Notification.objects.filter(
        user=request.user
    ).values_list('notification_type', flat=True).distinct()
    
    context = {
        'notifications': notifications,
        'notification_type': notification_type,
        'read_status': read_status,
        'available_types': available_types,
        'notification_type_choices': Notification.NOTIFICATION_TYPES,
    }
    
    return render(request, 'frontend/communication/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Redirect to action URL if available
    if notification.action_url:
        return redirect(notification.action_url)
    
    return redirect('frontend:notification_center')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    django_messages.success(request, 'All notifications marked as read')
    return redirect('frontend:notification_center')


@login_required
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    django_messages.success(request, 'Notification deleted')
    return redirect('frontend:notification_center')
