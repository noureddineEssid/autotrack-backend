from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Q
from .models import Reminder, NotificationPreference, PushToken
from .serializers import (
    ReminderSerializer,
    CreateReminderSerializer,
    NotificationPreferenceSerializer,
    PushTokenSerializer,
    ReminderStatsSerializer
)


class ReminderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reminders"""
    
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter reminders by current user"""
        queryset = Reminder.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        reminder_type = self.request.query_params.get('type')
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter unread only
        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            queryset = queryset.filter(status__in=['pending', 'sent'])
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new reminder"""
        serializer = CreateReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create reminder
        reminder = Reminder.objects.create(
            user=request.user,
            reminder_type=serializer.validated_data['reminder_type'],
            title=serializer.validated_data['title'],
            message=serializer.validated_data['message'],
            priority=serializer.validated_data.get('priority', 'medium'),
            vehicle_id=serializer.validated_data.get('vehicle_id'),
            maintenance_id=serializer.validated_data.get('maintenance_id'),
            document_id=serializer.validated_data.get('document_id'),
            diagnostic_id=serializer.validated_data.get('diagnostic_id'),
            remind_at=serializer.validated_data['remind_at'],
            repeat=serializer.validated_data.get('repeat', False),
            repeat_interval=serializer.validated_data.get('repeat_interval', ''),
        )
        
        response_serializer = ReminderSerializer(reminder)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark reminder as read"""
        reminder = self.get_object()
        reminder.mark_as_read()
        serializer = self.get_serializer(reminder)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss reminder"""
        reminder = self.get_object()
        reminder.dismiss()
        serializer = self.get_serializer(reminder)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all reminders as read"""
        unread = self.get_queryset().filter(status='sent')
        count = 0
        
        for reminder in unread:
            reminder.mark_as_read()
            count += 1
        
        return Response({'message': f'{count} reminders marked as read'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get reminder statistics"""
        queryset = self.get_queryset()
        
        total_reminders = queryset.count()
        pending = queryset.filter(status='pending').count()
        sent = queryset.filter(status='sent').count()
        read = queryset.filter(status='read').count()
        
        # Count overdue
        now = timezone.now()
        overdue = queryset.filter(status='pending', remind_at__lt=now).count()
        
        # Count by type
        by_type = dict(
            queryset.values('reminder_type')
            .annotate(count=Count('id'))
            .values_list('reminder_type', 'count')
        )
        
        # Count by priority
        by_priority = dict(
            queryset.values('priority')
            .annotate(count=Count('id'))
            .values_list('priority', 'count')
        )
        
        # Upcoming in next 7 days
        upcoming_date = now + timezone.timedelta(days=7)
        upcoming_7_days = queryset.filter(
            status='pending',
            remind_at__gte=now,
            remind_at__lte=upcoming_date
        ).count()
        
        stats_data = {
            'total_reminders': total_reminders,
            'pending': pending,
            'sent': sent,
            'read': read,
            'overdue': overdue,
            'by_type': by_type,
            'by_priority': by_priority,
            'upcoming_7_days': upcoming_7_days,
        }
        
        serializer = ReminderStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread reminders"""
        count = self.get_queryset().filter(status__in=['pending', 'sent']).count()
        return Response({'count': count})


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """ViewSet for notification preferences"""
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)
    
    def update(self, request, pk=None):
        """Update notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PushTokenViewSet(viewsets.ModelViewSet):
    """ViewSet for push notification tokens"""
    
    serializer_class = PushTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tokens by current user"""
        return PushToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Save token with current user"""
        # Deactivate existing token if same token exists
        token = serializer.validated_data['token']
        PushToken.objects.filter(token=token).update(is_active=False)
        
        serializer.save(user=self.request.user)
