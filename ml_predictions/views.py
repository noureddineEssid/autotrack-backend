from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import (
    VehicleHealthScore,
    FailurePrediction,
    MaintenanceRecommendation,
    MLModel,
    PredictionFeedback
)
from .serializers import (
    VehicleHealthScoreSerializer,
    FailurePredictionSerializer,
    MaintenanceRecommendationSerializer,
    MLModelSerializer,
    PredictionFeedbackSerializer,
    PredictionStatsSerializer
)
from .ml_engine import VehicleHealthPredictor, FailurePredictor, MaintenanceRecommender


class VehicleHealthScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les scores de santé des véhicules
    """
    serializer_class = VehicleHealthScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = VehicleHealthScore.objects.filter(
            vehicle__owner=self.request.user
        ).select_related('vehicle')
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calcule le score de santé pour un véhicule
        POST /api/ml-predictions/health-scores/calculate/
        Body: { "vehicle_id": "xxx" }
        """
        from vehicles.models import Vehicle
        
        vehicle_id = request.data.get('vehicle_id')
        if not vehicle_id:
            return Response(
                {'error': 'vehicle_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, owner=request.user)
        except Vehicle.DoesNotExist:
            return Response(
                {'error': 'Véhicule non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate health score
        health_score = VehicleHealthPredictor.calculate_health_score(vehicle)
        serializer = self.get_serializer(health_score)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Récupère les derniers scores pour tous les véhicules de l'utilisateur
        GET /api/ml-predictions/health-scores/latest/
        """
        from vehicles.models import Vehicle
        
        vehicles = Vehicle.objects.filter(owner=request.user)
        latest_scores = []
        
        for vehicle in vehicles:
            score = vehicle.health_scores.first()  # Already ordered by -calculated_at
            if score:
                latest_scores.append(score)
        
        serializer = self.get_serializer(latest_scores, many=True)
        return Response(serializer.data)


class FailurePredictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les prédictions de pannes
    """
    serializer_class = FailurePredictionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FailurePrediction.objects.filter(
            vehicle__owner=self.request.user
        ).select_related('vehicle')
        
        # Filters
        vehicle_id = self.request.query_params.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        component = self.request.query_params.get('component')
        if component:
            queryset = queryset.filter(component=component)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        urgent_only = self.request.query_params.get('urgent')
        if urgent_only == 'true':
            queryset = [pred for pred in queryset if pred.is_urgent]
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Génère des prédictions pour un véhicule
        POST /api/ml-predictions/predictions/generate/
        Body: { "vehicle_id": "xxx" }
        """
        from vehicles.models import Vehicle
        
        vehicle_id = request.data.get('vehicle_id')
        if not vehicle_id:
            return Response(
                {'error': 'vehicle_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, owner=request.user)
        except Vehicle.DoesNotExist:
            return Response(
                {'error': 'Véhicule non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate predictions
        predictions = FailurePredictor.predict_failures(vehicle)
        serializer = self.get_serializer(predictions, many=True)
        
        return Response(
            {
                'count': len(predictions),
                'predictions': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Marquer une prédiction comme prise en compte
        POST /api/ml-predictions/predictions/{id}/acknowledge/
        """
        prediction = self.get_object()
        prediction.acknowledge()
        serializer = self.get_serializer(prediction)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Marquer une prédiction comme résolue
        POST /api/ml-predictions/predictions/{id}/resolve/
        Body: { "feedback": "..." }
        """
        prediction = self.get_object()
        feedback = request.data.get('feedback', '')
        prediction.resolve(feedback)
        serializer = self.get_serializer(prediction)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def false_positive(self, request, pk=None):
        """
        Marquer comme faux positif
        POST /api/ml-predictions/predictions/{id}/false_positive/
        Body: { "feedback": "..." }
        """
        prediction = self.get_object()
        feedback = request.data.get('feedback', '')
        prediction.mark_false_positive(feedback)
        serializer = self.get_serializer(prediction)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """
        Récupère uniquement les prédictions urgentes
        GET /api/ml-predictions/predictions/urgent/
        """
        predictions = self.get_queryset().filter(
            Q(severity='critical') | 
            (Q(failure_probability__gte=0.8) & Q(estimated_days_until_failure__lte=30))
        )
        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Récupère uniquement les prédictions actives
        GET /api/ml-predictions/predictions/active/
        """
        predictions = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(predictions, many=True)
        return Response(serializer.data)


class MaintenanceRecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les recommandations de maintenance
    """
    serializer_class = MaintenanceRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = MaintenanceRecommendation.objects.filter(
            vehicle__owner=self.request.user
        ).select_related('vehicle', 'failure_prediction')
        
        # Filters
        vehicle_id = self.request.query_params.get('vehicle')
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        rec_type = self.request.query_params.get('type')
        if rec_type:
            queryset = queryset.filter(type=rec_type)
        
        is_completed = self.request.query_params.get('completed')
        if is_completed == 'true':
            queryset = queryset.filter(is_completed=True)
        elif is_completed == 'false':
            queryset = queryset.filter(is_completed=False, dismissed=False)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Génère des recommandations pour un véhicule
        POST /api/ml-predictions/recommendations/generate/
        Body: { "vehicle_id": "xxx" }
        """
        from vehicles.models import Vehicle
        
        vehicle_id = request.data.get('vehicle_id')
        if not vehicle_id:
            return Response(
                {'error': 'vehicle_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, owner=request.user)
        except Vehicle.DoesNotExist:
            return Response(
                {'error': 'Véhicule non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate recommendations
        recommendations = MaintenanceRecommender.generate_recommendations(vehicle)
        serializer = self.get_serializer(recommendations, many=True)
        
        return Response(
            {
                'count': len(recommendations),
                'recommendations': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Marquer une recommandation comme effectuée
        POST /api/ml-predictions/recommendations/{id}/complete/
        """
        recommendation = self.get_object()
        recommendation.mark_completed()
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """
        Rejeter une recommandation
        POST /api/ml-predictions/recommendations/{id}/dismiss/
        Body: { "reason": "..." }
        """
        recommendation = self.get_object()
        reason = request.data.get('reason', '')
        recommendation.dismiss(reason)
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Récupère les recommandations en attente
        GET /api/ml-predictions/recommendations/pending/
        """
        recommendations = self.get_queryset().filter(
            is_completed=False,
            dismissed=False
        )
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """
        Récupère les recommandations urgentes
        GET /api/ml-predictions/recommendations/urgent/
        """
        recommendations = self.get_queryset().filter(
            priority='urgent',
            is_completed=False,
            dismissed=False
        )
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)


class MLModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les modèles ML (admin/read-only)
    """
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated]
    queryset = MLModel.objects.all()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Récupère les modèles actifs
        GET /api/ml-predictions/models/active/
        """
        models = MLModel.objects.filter(is_active=True)
        serializer = self.get_serializer(models, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activer un modèle (admin only)
        POST /api/ml-predictions/models/{id}/activate/
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin requis'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        model = self.get_object()
        model.activate()
        serializer = self.get_serializer(model)
        return Response(serializer.data)


class PredictionFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les feedbacks sur les prédictions
    """
    serializer_class = PredictionFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PredictionFeedback.objects.filter(
            user=self.request.user
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PredictionStatsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les statistiques des prédictions
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Statistiques globales des prédictions
        GET /api/ml-predictions/stats/overview/
        """
        from vehicles.models import Vehicle
        
        vehicles = Vehicle.objects.filter(owner=request.user)
        
        # Health scores
        health_scores = VehicleHealthScore.objects.filter(
            vehicle__owner=request.user
        )
        avg_health = health_scores.aggregate(Avg('score'))['score__avg'] or 0
        
        # Predictions
        predictions = FailurePrediction.objects.filter(
            vehicle__owner=request.user
        )
        total_predictions = predictions.count()
        active_predictions = predictions.filter(status='active').count()
        critical_predictions = predictions.filter(severity='critical').count()
        
        # Predictions by component
        predictions_by_component = dict(
            predictions.values('component').annotate(count=Count('id')).values_list('component', 'count')
        )
        
        # Predictions by severity
        predictions_by_severity = dict(
            predictions.values('severity').annotate(count=Count('id')).values_list('severity', 'count')
        )
        
        # Recommendations
        recommendations = MaintenanceRecommendation.objects.filter(
            vehicle__owner=request.user
        )
        total_recommendations = recommendations.count()
        urgent_recommendations = recommendations.filter(
            priority='urgent',
            is_completed=False,
            dismissed=False
        ).count()
        
        # Average confidence
        avg_confidence = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
        
        stats = {
            'total_vehicles_analyzed': vehicles.count(),
            'avg_health_score': round(avg_health, 2),
            'total_predictions': total_predictions,
            'active_predictions': active_predictions,
            'critical_predictions': critical_predictions,
            'total_recommendations': total_recommendations,
            'urgent_recommendations': urgent_recommendations,
            'predictions_by_component': predictions_by_component,
            'predictions_by_severity': predictions_by_severity,
            'avg_confidence': round(avg_confidence, 2),
        }
        
        serializer = PredictionStatsSerializer(stats)
        return Response(serializer.data)
