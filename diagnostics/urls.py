from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiagnosticViewSet, DiagnosticReplyViewSet

app_name = 'diagnostics'

router = DefaultRouter()
router.register(r'diagnostics', DiagnosticViewSet, basename='diagnostic')
router.register(r'replies', DiagnosticReplyViewSet, basename='reply')

urlpatterns = [
    path('', include(router.urls)),
]
