from rest_framework import serializers
from .models import (
    VehicleHealthScore,
    FailurePrediction,
    MaintenanceRecommendation,
    MLModel,
    PredictionFeedback
)


class VehicleHealthScoreSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    score_level = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleHealthScore
        fields = [
            'id', 'vehicle', 'vehicle_info', 'score', 'score_level',
            'age_factor', 'mileage_factor', 'maintenance_factor',
            'repair_history_factor', 'usage_pattern_factor',
            'model_version', 'confidence', 'calculated_at'
        ]
        read_only_fields = fields
    
    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"
    
    def get_score_level(self, obj):
        if obj.score >= 80:
            return 'excellent'
        elif obj.score >= 60:
            return 'good'
        elif obj.score >= 40:
            return 'fair'
        else:
            return 'poor'


class FailurePredictionSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    component_display = serializers.CharField(source='get_component_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    risk_level = serializers.FloatField(read_only=True)
    
    class Meta:
        model = FailurePrediction
        fields = [
            'id', 'vehicle', 'vehicle_info', 'component', 'component_display',
            'severity', 'severity_display', 'status', 'status_display',
            'failure_probability', 'predicted_failure_date',
            'estimated_days_until_failure', 'confidence',
            'current_mileage', 'vehicle_age_years',
            'last_maintenance_date', 'days_since_last_maintenance',
            'description', 'symptoms', 'recommended_actions',
            'estimated_repair_cost', 'model_version', 'feature_importance',
            'is_urgent', 'risk_level',
            'created_at', 'updated_at', 'acknowledged_at', 'resolved_at',
            'user_feedback', 'was_accurate'
        ]
        read_only_fields = [
            'vehicle', 'component', 'severity', 'failure_probability',
            'predicted_failure_date', 'estimated_days_until_failure',
            'confidence', 'current_mileage', 'vehicle_age_years',
            'description', 'symptoms', 'recommended_actions',
            'estimated_repair_cost', 'model_version', 'feature_importance',
            'created_at', 'updated_at'
        ]
    
    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"


class MaintenanceRecommendationSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    failure_prediction_details = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceRecommendation
        fields = [
            'id', 'vehicle', 'vehicle_info', 'title', 'description',
            'priority', 'priority_display', 'type', 'type_display',
            'failure_prediction', 'failure_prediction_details',
            'component', 'recommended_service', 'estimated_cost',
            'estimated_duration_hours', 'recommended_by_date',
            'recommended_by_mileage', 'confidence', 'based_on_factors',
            'is_completed', 'completed_at', 'dismissed', 'dismissed_reason',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'vehicle', 'title', 'description', 'priority', 'type',
            'failure_prediction', 'component', 'recommended_service',
            'estimated_cost', 'estimated_duration_hours',
            'recommended_by_date', 'recommended_by_mileage',
            'confidence', 'based_on_factors', 'created_at', 'updated_at'
        ]
    
    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"
    
    def get_failure_prediction_details(self, obj):
        if obj.failure_prediction:
            return {
                'component': obj.failure_prediction.get_component_display(),
                'probability': obj.failure_prediction.failure_probability,
                'severity': obj.failure_prediction.get_severity_display(),
            }
        return None


class MLModelSerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'version', 'model_type', 'model_type_display',
            'algorithm', 'accuracy', 'precision', 'recall', 'f1_score',
            'mae', 'rmse', 'training_date', 'training_samples',
            'features_used', 'hyperparameters', 'model_file_path',
            'is_active', 'is_production', 'notes', 'created_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None


class PredictionFeedbackSerializer(serializers.ModelSerializer):
    feedback_type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PredictionFeedback
        fields = [
            'id', 'user', 'user_name', 'feedback_type',
            'feedback_type_display', 'health_score', 'failure_prediction',
            'recommendation', 'rating', 'rating_display', 'was_accurate',
            'comment', 'actual_failure_occurred', 'actual_failure_date',
            'actual_repair_cost', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    
    def validate(self, data):
        # Ensure at least one related object is provided
        if not any([data.get('health_score'), data.get('failure_prediction'), data.get('recommendation')]):
            raise serializers.ValidationError(
                "Au moins un objet lié (health_score, failure_prediction, ou recommendation) doit être fourni."
            )
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PredictionStatsSerializer(serializers.Serializer):
    """Serializer for prediction statistics"""
    total_vehicles_analyzed = serializers.IntegerField()
    avg_health_score = serializers.FloatField()
    total_predictions = serializers.IntegerField()
    active_predictions = serializers.IntegerField()
    critical_predictions = serializers.IntegerField()
    total_recommendations = serializers.IntegerField()
    urgent_recommendations = serializers.IntegerField()
    predictions_by_component = serializers.DictField()
    predictions_by_severity = serializers.DictField()
    avg_confidence = serializers.FloatField()
