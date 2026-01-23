"""
URL configuration for bookings app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GarageServiceViewSet,
    GarageAvailabilityViewSet,
    BookingViewSet,
    BookingReviewViewSet
)

router = DefaultRouter()
router.register(r'services', GarageServiceViewSet, basename='garage-service')
router.register(r'availability', GarageAvailabilityViewSet, basename='garage-availability')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', BookingReviewViewSet, basename='booking-review')

urlpatterns = [
    path('', include(router.urls)),
]
