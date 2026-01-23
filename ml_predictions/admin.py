from django.contrib import admin
from .models import (
    VehicleHealthScore,
    FailurePrediction,
    MaintenanceRecommendation,
    MLModel,
    PredictionFeedback
)


@admin.register(VehicleHealthScore)
class VehicleHealthScoreAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'score', 'confidence', 'model_version', 'calculated_at']
    list_filter = ['model_version', 'calculated_at']
    search_fields = ['vehicle__license_plate', 'vehicle__make', 'vehicle__model']
    readonly_fields = ['calculated_at']
    date_hierarchy = 'calculated_at'
    
    fieldsets = (
        ('Véhicule', {
            'fields': ('vehicle',)
        }),
        ('Score', {
            'fields': ('score', 'confidence')
        }),
        ('Facteurs', {
            'fields': (
                'age_factor',
                'mileage_factor',
                'maintenance_factor',
                'repair_history_factor',
                'usage_pattern_factor'
            )
        }),
        ('Métadonnées', {
            'fields': ('model_version', 'calculated_at')
        }),
    )


@admin.register(FailurePrediction)
class FailurePredictionAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle',
        'component',
        'severity',
        'status',
        'failure_probability',
        'predicted_failure_date',
        'is_urgent',
        'created_at'
    ]
    list_filter = ['component', 'severity', 'status', 'created_at']
    search_fields = ['vehicle__license_plate', 'vehicle__make', 'description']
    readonly_fields = ['created_at', 'updated_at', 'is_urgent', 'risk_level']
    date_hierarchy = 'created_at'
    actions = ['mark_acknowledged', 'mark_resolved']
    
    fieldsets = (
        ('Véhicule et Composant', {
            'fields': ('vehicle', 'component')
        }),
        ('Prédiction', {
            'fields': (
                'failure_probability',
                'predicted_failure_date',
                'estimated_days_until_failure',
                'severity',
                'confidence',
                'is_urgent',
                'risk_level'
            )
        }),
        ('Contexte', {
            'fields': (
                'current_mileage',
                'vehicle_age_years',
                'last_maintenance_date',
                'days_since_last_maintenance'
            )
        }),
        ('Détails', {
            'fields': (
                'description',
                'symptoms',
                'recommended_actions',
                'estimated_repair_cost'
            )
        }),
        ('ML', {
            'fields': ('model_version', 'feature_importance'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': (
                'status',
                'acknowledged_at',
                'resolved_at',
                'user_feedback',
                'was_accurate'
            )
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_acknowledged(self, request, queryset):
        for prediction in queryset:
            prediction.acknowledge()
        self.message_user(request, f"{queryset.count()} prédiction(s) marquée(s) comme prise(s) en compte")
    mark_acknowledged.short_description = "Marquer comme pris en compte"
    
    def mark_resolved(self, request, queryset):
        for prediction in queryset:
            prediction.resolve()
        self.message_user(request, f"{queryset.count()} prédiction(s) résolue(s)")
    mark_resolved.short_description = "Marquer comme résolu"


@admin.register(MaintenanceRecommendation)
class MaintenanceRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle',
        'title',
        'priority',
        'type',
        'is_completed',
        'dismissed',
        'is_overdue',
        'created_at'
    ]
    list_filter = ['priority', 'type', 'is_completed', 'dismissed', 'created_at']
    search_fields = ['vehicle__license_plate', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue']
    date_hierarchy = 'created_at'
    actions = ['mark_completed', 'mark_dismissed']
    
    fieldsets = (
        ('Véhicule', {
            'fields': ('vehicle',)
        }),
        ('Recommandation', {
            'fields': (
                'title',
                'description',
                'priority',
                'type',
                'component',
                'recommended_service'
            )
        }),
        ('Prédiction liée', {
            'fields': ('failure_prediction',)
        }),
        ('Estimation', {
            'fields': (
                'estimated_cost',
                'estimated_duration_hours',
                'recommended_by_date',
                'recommended_by_mileage'
            )
        }),
        ('ML', {
            'fields': ('confidence', 'based_on_factors'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': (
                'is_completed',
                'completed_at',
                'dismissed',
                'dismissed_reason',
                'is_overdue'
            )
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_completed(self, request, queryset):
        for rec in queryset:
            rec.mark_completed()
        self.message_user(request, f"{queryset.count()} recommandation(s) marquée(s) comme effectuée(s)")
    mark_completed.short_description = "Marquer comme effectué"
    
    def mark_dismissed(self, request, queryset):
        for rec in queryset:
            rec.dismiss()
        self.message_user(request, f"{queryset.count()} recommandation(s) rejetée(s)")
    mark_dismissed.short_description = "Rejeter"


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'version',
        'model_type',
        'algorithm',
        'is_active',
        'is_production',
        'training_date',
        'training_samples'
    ]
    list_filter = ['model_type', 'is_active', 'is_production', 'training_date']
    search_fields = ['name', 'version', 'algorithm']
    readonly_fields = ['created_at']
    date_hierarchy = 'training_date'
    actions = ['activate_model']
    
    fieldsets = (
        ('Identité', {
            'fields': ('name', 'version', 'model_type', 'algorithm')
        }),
        ('Performance', {
            'fields': (
                'accuracy',
                'precision',
                'recall',
                'f1_score',
                'mae',
                'rmse'
            )
        }),
        ('Entraînement', {
            'fields': (
                'training_date',
                'training_samples',
                'features_used',
                'hyperparameters'
            )
        }),
        ('Fichier', {
            'fields': ('model_file_path',)
        }),
        ('Statut', {
            'fields': ('is_active', 'is_production')
        }),
        ('Métadonnées', {
            'fields': ('notes', 'created_at', 'created_by')
        }),
    )
    
    def activate_model(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Sélectionnez un seul modèle à activer", level='error')
            return
        
        model = queryset.first()
        model.activate()
        self.message_user(request, f"Modèle {model.version} activé")
    activate_model.short_description = "Activer le modèle"


@admin.register(PredictionFeedback)
class PredictionFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'feedback_type',
        'rating',
        'was_accurate',
        'created_at'
    ]
    list_filter = ['feedback_type', 'rating', 'was_accurate', 'created_at']
    search_fields = ['user__username', 'comment']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Type', {
            'fields': (
                'feedback_type',
                'health_score',
                'failure_prediction',
                'recommendation'
            )
        }),
        ('Feedback', {
            'fields': (
                'rating',
                'was_accurate',
                'comment'
            )
        }),
        ('Résultat réel', {
            'fields': (
                'actual_failure_occurred',
                'actual_failure_date',
                'actual_repair_cost'
            )
        }),
        ('Horodatage', {
            'fields': ('created_at',)
        }),
    )
