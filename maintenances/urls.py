from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaintenanceViewSet

app_name = 'maintenances'

router = DefaultRouter()
router.register(r'maintenances', MaintenanceViewSet, basename='maintenance')

urlpatterns = [
    path('', include(router.urls)),
]
