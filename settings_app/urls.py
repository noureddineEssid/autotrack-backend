from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserSettingsViewSet

app_name = 'settings_app'

router = DefaultRouter()
router.register(r'settings', UserSettingsViewSet, basename='user-settings')

urlpatterns = [
    path('', include(router.urls)),
]
