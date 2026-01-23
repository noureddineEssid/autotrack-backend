from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReminderViewSet, NotificationPreferenceViewSet, PushTokenViewSet

router = DefaultRouter()
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'push-tokens', PushTokenViewSet, basename='push-token')

urlpatterns = [
    path('', include(router.urls)),
]
