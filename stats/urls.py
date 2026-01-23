"""
Statistics URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StatisticsViewSet

router = DefaultRouter()
router.register(r'', StatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
]
