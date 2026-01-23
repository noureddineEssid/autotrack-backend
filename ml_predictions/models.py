from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


class VehicleHealthScore(models.Model):
    """
    Score de santé d'un véhicule calculé par ML
    """
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='health_scores')
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Score de 0 (très mauvais) à 100 (excellent)"
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    # Factors contributing to score
    age_factor = models.FloatField(default=0.0)
    mileage_factor = models.FloatField(default=0.0)
    maintenance_factor = models.FloatField(default=0.0)
    repair_history_factor = models.FloatField(default=0.0)
    usage_pattern_factor = models.FloatField(default=0.0)
    
    # Metadata
    model_version = models.CharField(max_length=50, help_text="Version du modèle ML utilisé")
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Niveau de confiance de la prédiction"
    )
    
    class Meta:
        ordering = ['-calculated_at']
        indexes = [
            models.Index(fields=['vehicle', '-calculated_at']),
            models.Index(fields=['score']),
        ]
    
    def __str__(self):
        return f"{self.vehicle} - Score: {self.score:.1f} ({self.calculated_at.date()})"


class FailurePrediction(models.Model):
    """
    Prédiction de panne pour un composant spécifique
    """
    COMPONENT_CHOICES = [
        ('engine', 'Moteur'),
        ('transmission', 'Transmission'),
        ('brakes', 'Freins'),
        ('suspension', 'Suspension'),
        ('electrical', 'Système électrique'),
        ('cooling', 'Système de refroidissement'),
        ('exhaust', 'Système d\'échappement'),
        ('fuel', 'Système de carburant'),
        ('tires', 'Pneus'),
        ('battery', 'Batterie'),
        ('alternator', 'Alternateur'),
        ('starter', 'Démarreur'),
        ('air_conditioning', 'Climatisation'),
        ('steering', 'Direction'),
        ('other', 'Autre'),
    ]
    
    SEVERITY_CHOICES = [
        ('critical', 'Critique'),
        ('high', 'Élevée'),
        ('medium', 'Moyenne'),
        ('low', 'Faible'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Pris en compte'),
        ('resolved', 'Résolue'),
        ('false_positive', 'Faux positif'),
    ]
    
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='failure_predictions')
    component = models.CharField(max_length=50, choices=COMPONENT_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Prediction details
    failure_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probabilité de panne (0-1)"
    )
    predicted_failure_date = models.DateField(null=True, blank=True)
    estimated_days_until_failure = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Contributing factors
    current_mileage = models.IntegerField()
    vehicle_age_years = models.FloatField()
    last_maintenance_date = models.DateField(null=True, blank=True)
    days_since_last_maintenance = models.IntegerField(null=True, blank=True)
    
    # Description and recommendations
    description = models.TextField(help_text="Description de la panne potentielle")
    symptoms = models.JSONField(default=list, help_text="Symptômes à surveiller")
    recommended_actions = models.JSONField(default=list, help_text="Actions recommandées")
    estimated_repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # ML metadata
    model_version = models.CharField(max_length=50)
    feature_importance = models.JSONField(
        default=dict,
        help_text="Importance des features dans la prédiction"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # User feedback
    user_feedback = models.TextField(blank=True)
    was_accurate = models.BooleanField(null=True, blank=True)
    
    class Meta:
        ordering = ['-failure_probability', '-severity', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-created_at']),
            models.Index(fields=['status', '-failure_probability']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['predicted_failure_date']),
        ]
    
    def __str__(self):
        return f"{self.vehicle} - {self.get_component_display()} ({self.failure_probability:.0%})"
    
    @property
    def is_urgent(self):
        """Panne urgente si critique ou probabilité >80% dans les 30 jours"""
        if self.severity == 'critical':
            return True
        if self.failure_probability >= 0.8 and self.estimated_days_until_failure and self.estimated_days_until_failure <= 30:
            return True
        return False
    
    @property
    def risk_level(self):
        """Calcul du niveau de risque combiné"""
        severity_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        severity_score = severity_weights.get(self.severity, 1)
        return severity_score * self.failure_probability
    
    def acknowledge(self):
        """Marquer comme pris en compte"""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, feedback=''):
        """Marquer comme résolue"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if feedback:
            self.user_feedback = feedback
        self.save()
    
    def mark_false_positive(self, feedback=''):
        """Marquer comme faux positif"""
        self.status = 'false_positive'
        self.was_accurate = False
        if feedback:
            self.user_feedback = feedback
        self.save()


class MaintenanceRecommendation(models.Model):
    """
    Recommandation de maintenance générée par ML
    """
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'Élevée'),
        ('medium', 'Moyenne'),
        ('low', 'Faible'),
    ]
    
    TYPE_CHOICES = [
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('predictive', 'Prédictive'),
    ]
    
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='ml_recommendations')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Related prediction (if any)
    failure_prediction = models.ForeignKey(
        FailurePrediction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    
    # Recommendation details
    component = models.CharField(max_length=100)
    recommended_service = models.CharField(max_length=200)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration_hours = models.FloatField(null=True, blank=True)
    
    # Timing
    recommended_by_date = models.DateField(null=True, blank=True)
    recommended_by_mileage = models.IntegerField(null=True, blank=True)
    
    # ML metadata
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    based_on_factors = models.JSONField(default=list)
    
    # Status
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)
    dismissed_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-created_at']),
            models.Index(fields=['priority', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.vehicle} - {self.title}"
    
    @property
    def is_overdue(self):
        """Vérifier si la recommandation est en retard"""
        if self.is_completed or self.dismissed:
            return False
        if self.recommended_by_date and self.recommended_by_date < timezone.now().date():
            return True
        return False
    
    def mark_completed(self):
        """Marquer comme effectuée"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def dismiss(self, reason=''):
        """Rejeter la recommandation"""
        self.dismissed = True
        self.dismissed_reason = reason
        self.save()


class MLModel(models.Model):
    """
    Métadonnées des modèles ML entraînés
    """
    MODEL_TYPE_CHOICES = [
        ('health_score', 'Score de santé'),
        ('failure_prediction', 'Prédiction de panne'),
        ('maintenance_recommendation', 'Recommandation maintenance'),
        ('cost_estimation', 'Estimation coûts'),
    ]
    
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, unique=True)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES)
    algorithm = models.CharField(max_length=100, help_text="Ex: RandomForest, XGBoost, Neural Network")
    
    # Model performance
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    mae = models.FloatField(null=True, blank=True, help_text="Mean Absolute Error")
    rmse = models.FloatField(null=True, blank=True, help_text="Root Mean Squared Error")
    
    # Training details
    training_date = models.DateTimeField()
    training_samples = models.IntegerField()
    features_used = models.JSONField(default=list)
    hyperparameters = models.JSONField(default=dict)
    
    # Model file
    model_file_path = models.CharField(max_length=500, help_text="Chemin vers le fichier du modèle")
    
    # Status
    is_active = models.BooleanField(default=False)
    is_production = models.BooleanField(default=False)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-training_date']
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
            models.Index(fields=['version']),
        ]
    
    def __str__(self):
        return f"{self.get_model_type_display()} v{self.version}"
    
    def activate(self):
        """Activer ce modèle (désactive les autres du même type)"""
        # Désactiver les autres modèles du même type
        MLModel.objects.filter(model_type=self.model_type, is_active=True).update(is_active=False)
        self.is_active = True
        self.save()


class PredictionFeedback(models.Model):
    """
    Feedback utilisateur sur les prédictions (pour améliorer le modèle)
    """
    FEEDBACK_TYPE_CHOICES = [
        ('health_score', 'Score de santé'),
        ('failure_prediction', 'Prédiction de panne'),
        ('recommendation', 'Recommandation'),
    ]
    
    RATING_CHOICES = [
        (1, 'Très mauvais'),
        (2, 'Mauvais'),
        (3, 'Moyen'),
        (4, 'Bon'),
        (5, 'Excellent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ml_feedback')
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPE_CHOICES)
    
    # Related objects
    health_score = models.ForeignKey(VehicleHealthScore, on_delete=models.CASCADE, null=True, blank=True)
    failure_prediction = models.ForeignKey(FailurePrediction, on_delete=models.CASCADE, null=True, blank=True)
    recommendation = models.ForeignKey(MaintenanceRecommendation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Feedback details
    rating = models.IntegerField(choices=RATING_CHOICES)
    was_accurate = models.BooleanField(help_text="La prédiction était-elle correcte?")
    comment = models.TextField(blank=True)
    
    # Actual outcome (if known)
    actual_failure_occurred = models.BooleanField(null=True, blank=True)
    actual_failure_date = models.DateField(null=True, blank=True)
    actual_repair_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback {self.get_feedback_type_display()} - {self.get_rating_display()}"
