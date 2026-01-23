from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ReportTemplateViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-templates', ReportTemplateViewSet, basename='report-template')

urlpatterns = [
    path('', include(router.urls)),
]
