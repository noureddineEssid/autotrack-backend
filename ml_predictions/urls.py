from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleHealthScoreViewSet,
    FailurePredictionViewSet,
    MaintenanceRecommendationViewSet,
    MLModelViewSet,
    PredictionFeedbackViewSet,
    PredictionStatsViewSet
)

router = DefaultRouter()
router.register(r'health-scores', VehicleHealthScoreViewSet, basename='health-score')
router.register(r'predictions', FailurePredictionViewSet, basename='prediction')
router.register(r'recommendations', MaintenanceRecommendationViewSet, basename='recommendation')
router.register(r'models', MLModelViewSet, basename='ml-model')
router.register(r'feedback', PredictionFeedbackViewSet, basename='feedback')
router.register(r'stats', PredictionStatsViewSet, basename='stats')

urlpatterns = router.urls
