"""Context processors for frontend app"""
from inventory.models import ReservationRequest
from prescription.models import Message, Notification


def manufacturer_context(request):
    """Add manufacturer-specific context variables"""
    context = {}
    
    if request.user.is_authenticated and hasattr(request.user, 'is_manufacturer') and request.user.is_manufacturer:
        # Get pending reservation requests count
        pending_count = ReservationRequest.objects.filter(
            manufacturer=request.user,
            status=ReservationRequest.STATUS_PENDING
        ).count()
        
        context['pending_reservations_count'] = pending_count
    
    return context


def unread_counts(request):
    """Add unread message and notification counts to all pages"""
    context = {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
    }
    
    if request.user.is_authenticated:
        # Count unread messages
        context['unread_messages_count'] = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        # Count unread notifications
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    
    return context
