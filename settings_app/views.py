from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSettings
from .serializers import UserSettingsSerializer, UserSettingsUpdateSerializer


class UserSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user settings
    
    list: Get current user's settings
    retrieve: Get specific settings
    update: Update settings
    partial_update: Partially update settings
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSettingsSerializer
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
    
    def get_queryset(self):
        """Filter settings by current user"""
        return UserSettings.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['update', 'partial_update']:
            return UserSettingsUpdateSerializer
        return UserSettingsSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Update current user's settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        serializer = UserSettingsUpdateSerializer(
            settings, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(UserSettingsSerializer(settings).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset settings to default"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        # Reset to defaults
        settings.language = 'en'
        settings.theme = 'auto'
        settings.timezone = 'UTC'
        settings.email_notifications = True
        settings.push_notifications = True
        settings.maintenance_reminders = True
        settings.subscription_alerts = True
        settings.profile_public = False
        settings.custom_settings = {}
        settings.save()
        
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

