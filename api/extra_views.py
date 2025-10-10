from rest_framework import generics, permissions
from rest_framework.response import Response
from django.utils import timezone

from prescription.models import PatientDoctorAssignment, Notification, Message


class AssignedDoctorsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        assignments = (PatientDoctorAssignment.objects
                       .filter(patient=request.user)
                       .select_related('doctor')
                       .order_by('-is_primary', '-assigned_date'))
        data = []
        for a in assignments:
            d = a.doctor
            data.append({
                'id': a.id,
                'is_primary': a.is_primary,
                'assigned_date': a.assigned_date.isoformat(),
                'doctor': {
                    'id': d.id,
                    'username': d.username,
                    'first_name': d.first_name,
                    'last_name': d.last_name,
                    'full_name': d.full_name,
                    'license_number': d.license_number,
                }
            })
        return Response({'results': data})


class NotificationListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all notifications for counting
        all_notifications = Notification.objects.filter(user=request.user)
        
        # Get recent notifications for display
        notifications = all_notifications.order_by('-created_at')[:20]
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
            })
        
        return Response({
            'results': data,
            'count': len(data),
            'unread_count': all_notifications.filter(is_read=False).count()
        })


class MessageListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all messages for counting
        all_messages = Message.objects.filter(recipient=request.user)
        
        # Get recent messages for display
        messages = all_messages.select_related('sender').order_by('-sent_at')[:20]
        
        data = []
        for message in messages:
            data.append({
                'id': message.id,
                'subject': message.subject,
                'body': message.body,
                'sent_at': message.sent_at.isoformat(),
                'is_read': message.is_read,
                'read_at': message.read_at.isoformat() if message.read_at else None,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name,
                    'full_name': message.sender.full_name,
                }
            })
        
        return Response({
            'results': data,
            'count': len(data),
            'unread_count': all_messages.filter(is_read=False).count()
        })


class UnreadCountsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        unread_messages = Message.objects.filter(
            recipient=request.user, 
            is_read=False
        ).count()
        
        return Response({
            'notifications': unread_notifications,
            'messages': unread_messages,
            'total': unread_notifications + unread_messages
        })


class NotificationReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read',
                'notification_id': notification_id
            })
        except Notification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification not found'
            }, status=404)


class NotificationReadAllView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
