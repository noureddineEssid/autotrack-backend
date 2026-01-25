from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GarageViewSet, GarageReviewViewSet

app_name = 'garages'

router = DefaultRouter()
router.register(r'garages', GarageViewSet, basename='garage')
router.register(r'reviews', GarageReviewViewSet, basename='review')
router.register(r'recommended', GarageViewSet, basename='recommended')

urlpatterns = [
    path('', include(router.urls)),
]
