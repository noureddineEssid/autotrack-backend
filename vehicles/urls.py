from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, CarBrandViewSet, CarModelViewSet

app_name = 'vehicles'

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'brands', CarBrandViewSet, basename='brand')
router.register(r'models', CarModelViewSet, basename='model')

urlpatterns = [
    path('', include(router.urls)),
]
