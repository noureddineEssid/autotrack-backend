"""
ML Engine pour les prédictions de pannes et calculs de santé
"""

import joblib
import numpy as np
from datetime import timedelta, date
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Sum, Q, F
from .models import VehicleHealthScore, FailurePrediction, MaintenanceRecommendation, MLModel


class VehicleHealthPredictor:
    """
    Calcule le score de santé d'un véhicule basé sur plusieurs facteurs
    """
    
    MODEL_VERSION = "1.0.0"
    
    # Weights for different factors (total = 1.0)
    WEIGHTS = {
        'age': 0.20,
        'mileage': 0.25,
        'maintenance': 0.30,
        'repair_history': 0.15,
        'usage_pattern': 0.10,
    }
    
    @classmethod
    def calculate_health_score(cls, vehicle):
        """
        Calcule le score de santé global d'un véhicule
        
        Returns: VehicleHealthScore instance
        """
        # Calculate individual factors
        age_factor = cls._calculate_age_factor(vehicle)
        mileage_factor = cls._calculate_mileage_factor(vehicle)
        maintenance_factor = cls._calculate_maintenance_factor(vehicle)
        repair_history_factor = cls._calculate_repair_history_factor(vehicle)
        usage_pattern_factor = cls._calculate_usage_pattern_factor(vehicle)
        
        # Weighted average
        total_score = (
            age_factor * cls.WEIGHTS['age'] +
            mileage_factor * cls.WEIGHTS['mileage'] +
            maintenance_factor * cls.WEIGHTS['maintenance'] +
            repair_history_factor * cls.WEIGHTS['repair_history'] +
            usage_pattern_factor * cls.WEIGHTS['usage_pattern']
        )
        
        # Confidence based on data availability
        confidence = cls._calculate_confidence(vehicle)
        
        # Create health score record
        health_score = VehicleHealthScore.objects.create(
            vehicle=vehicle,
            score=round(total_score, 2),
            age_factor=age_factor,
            mileage_factor=mileage_factor,
            maintenance_factor=maintenance_factor,
            repair_history_factor=repair_history_factor,
            usage_pattern_factor=usage_pattern_factor,
            model_version=cls.MODEL_VERSION,
            confidence=confidence
        )
        
        return health_score
    
    @classmethod
    def _calculate_age_factor(cls, vehicle):
        """Score basé sur l'âge du véhicule (0-100)"""
        age_years = vehicle.age_years
        
        if age_years <= 2:
            return 100.0
        elif age_years <= 5:
            return 90.0 - ((age_years - 2) * 5)  # 90-75
        elif age_years <= 10:
            return 75.0 - ((age_years - 5) * 5)  # 75-50
        elif age_years <= 15:
            return 50.0 - ((age_years - 10) * 4)  # 50-30
        else:
            return max(30.0 - ((age_years - 15) * 2), 10.0)
    
    @classmethod
    def _calculate_mileage_factor(cls, vehicle):
        """Score basé sur le kilométrage"""
        if not vehicle.current_mileage:
            return 50.0  # Default if no mileage
        
        mileage = vehicle.current_mileage
        age_years = vehicle.age_years or 1
        
        # Average km per year
        avg_km_per_year = mileage / age_years
        
        if avg_km_per_year <= 10000:
            return 100.0
        elif avg_km_per_year <= 15000:
            return 90.0
        elif avg_km_per_year <= 20000:
            return 75.0
        elif avg_km_per_year <= 30000:
            return 60.0
        elif avg_km_per_year <= 40000:
            return 40.0
        else:
            return 20.0
    
    @classmethod
    def _calculate_maintenance_factor(cls, vehicle):
        """Score basé sur l'historique de maintenance"""
        from maintenance.models import MaintenanceRecord
        
        # Get maintenance records from last 2 years
        two_years_ago = timezone.now() - timedelta(days=730)
        recent_maintenance = MaintenanceRecord.objects.filter(
            vehicle=vehicle,
            date__gte=two_years_ago
        ).count()
        
        # Recommended maintenance per year (varies by vehicle age)
        age_years = vehicle.age_years or 0
        if age_years <= 3:
            recommended_per_year = 1  # Newer cars: 1 per year
        elif age_years <= 7:
            recommended_per_year = 2  # Mid-age: 2 per year
        else:
            recommended_per_year = 3  # Older cars: 3 per year
        
        expected_maintenance = recommended_per_year * 2  # For 2 years
        
        if recent_maintenance >= expected_maintenance:
            return 100.0
        elif recent_maintenance >= expected_maintenance * 0.75:
            return 85.0
        elif recent_maintenance >= expected_maintenance * 0.50:
            return 70.0
        elif recent_maintenance >= expected_maintenance * 0.25:
            return 50.0
        else:
            return 30.0
    
    @classmethod
    def _calculate_repair_history_factor(cls, vehicle):
        """Score basé sur l'historique de réparations"""
        from repairs.models import Repair
        
        # Get repairs from last year
        one_year_ago = timezone.now() - timedelta(days=365)
        recent_repairs = Repair.objects.filter(
            vehicle=vehicle,
            date__gte=one_year_ago
        )
        
        repair_count = recent_repairs.count()
        total_cost = recent_repairs.aggregate(Sum('cost'))['cost__sum'] or 0
        
        # More repairs = lower score
        if repair_count == 0:
            count_score = 100.0
        elif repair_count <= 2:
            count_score = 80.0
        elif repair_count <= 4:
            count_score = 60.0
        elif repair_count <= 6:
            count_score = 40.0
        else:
            count_score = 20.0
        
        # Higher costs = lower score
        if total_cost == 0:
            cost_score = 100.0
        elif total_cost <= 500:
            cost_score = 85.0
        elif total_cost <= 1500:
            cost_score = 70.0
        elif total_cost <= 3000:
            cost_score = 50.0
        else:
            cost_score = 30.0
        
        return (count_score + cost_score) / 2
    
    @classmethod
    def _calculate_usage_pattern_factor(cls, vehicle):
        """Score basé sur les patterns d'utilisation"""
        # For now, return a default score
        # In production, this would analyze fuel consumption, trips, etc.
        return 75.0
    
    @classmethod
    def _calculate_confidence(cls, vehicle):
        """Calcule le niveau de confiance basé sur la disponibilité des données"""
        data_points = 0
        
        # Check data availability
        if vehicle.year:
            data_points += 1
        if vehicle.current_mileage:
            data_points += 1
        
        from maintenance.models import MaintenanceRecord
        from repairs.models import Repair
        
        if MaintenanceRecord.objects.filter(vehicle=vehicle).exists():
            data_points += 1
        if Repair.objects.filter(vehicle=vehicle).exists():
            data_points += 1
        
        # Confidence: 0.5 (minimum) to 1.0 (maximum)
        return 0.5 + (data_points * 0.125)  # Max 4 data points = 1.0


class FailurePredictor:
    """
    Prédit les pannes potentielles basé sur les données historiques
    """
    
    MODEL_VERSION = "1.0.0"
    
    # Component failure thresholds
    COMPONENT_THRESHOLDS = {
        'battery': {'mileage': 150000, 'years': 5},
        'brakes': {'mileage': 60000, 'years': 3},
        'tires': {'mileage': 50000, 'years': 5},
        'engine': {'mileage': 250000, 'years': 15},
        'transmission': {'mileage': 200000, 'years': 12},
        'alternator': {'mileage': 120000, 'years': 7},
        'starter': {'mileage': 150000, 'years': 10},
        'suspension': {'mileage': 100000, 'years': 8},
        'cooling': {'mileage': 150000, 'years': 10},
    }
    
    @classmethod
    def predict_failures(cls, vehicle):
        """
        Génère des prédictions de pannes pour un véhicule
        
        Returns: List of FailurePrediction instances
        """
        predictions = []
        
        # Clear old active predictions for this vehicle
        FailurePrediction.objects.filter(
            vehicle=vehicle,
            status='active'
        ).update(status='resolved')
        
        # Check each component
        for component, thresholds in cls.COMPONENT_THRESHOLDS.items():
            prediction = cls._predict_component_failure(vehicle, component, thresholds)
            if prediction:
                predictions.append(prediction)
        
        return predictions
    
    @classmethod
    def _predict_component_failure(cls, vehicle, component, thresholds):
        """Prédit la panne d'un composant spécifique"""
        mileage = vehicle.current_mileage or 0
        age_years = vehicle.age_years or 0
        
        # Calculate usage ratios
        mileage_ratio = mileage / thresholds['mileage'] if thresholds['mileage'] > 0 else 0
        age_ratio = age_years / thresholds['years'] if thresholds['years'] > 0 else 0
        
        # Weighted average (mileage more important)
        failure_score = (mileage_ratio * 0.6) + (age_ratio * 0.4)
        
        # Only create prediction if score > 0.5 (50%)
        if failure_score < 0.5:
            return None
        
        # Calculate probability (capped at 0.95)
        probability = min(failure_score, 0.95)
        
        # Estimate days until failure
        days_until_failure = cls._estimate_days_until_failure(
            failure_score,
            mileage,
            age_years
        )
        
        # Determine severity
        if probability >= 0.8:
            severity = 'critical'
        elif probability >= 0.65:
            severity = 'high'
        elif probability >= 0.50:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Get component-specific details
        details = cls._get_component_details(component, vehicle)
        
        prediction = FailurePrediction.objects.create(
            vehicle=vehicle,
            component=component,
            severity=severity,
            failure_probability=round(probability, 2),
            predicted_failure_date=date.today() + timedelta(days=days_until_failure) if days_until_failure else None,
            estimated_days_until_failure=days_until_failure,
            confidence=0.75,  # Base confidence
            current_mileage=mileage,
            vehicle_age_years=age_years,
            description=details['description'],
            symptoms=details['symptoms'],
            recommended_actions=details['actions'],
            estimated_repair_cost=details['cost'],
            model_version=cls.MODEL_VERSION,
            feature_importance={
                'mileage_ratio': round(mileage_ratio, 2),
                'age_ratio': round(age_ratio, 2),
                'failure_score': round(failure_score, 2),
            }
        )
        
        return prediction
    
    @classmethod
    def _estimate_days_until_failure(cls, failure_score, mileage, age_years):
        """Estime le nombre de jours avant la panne"""
        if failure_score >= 0.9:
            return np.random.randint(30, 60)  # 1-2 months
        elif failure_score >= 0.75:
            return np.random.randint(60, 120)  # 2-4 months
        elif failure_score >= 0.60:
            return np.random.randint(120, 180)  # 4-6 months
        else:
            return np.random.randint(180, 365)  # 6-12 months
    
    @classmethod
    def _get_component_details(cls, component, vehicle):
        """Retourne les détails spécifiques au composant"""
        details_map = {
            'battery': {
                'description': 'La batterie montre des signes de faiblesse et pourrait nécessiter un remplacement bientôt.',
                'symptoms': [
                    'Démarrage difficile',
                    'Lumières faibles',
                    'Problèmes électriques intermittents'
                ],
                'actions': [
                    'Tester la tension de la batterie',
                    'Vérifier les connexions',
                    'Remplacer si nécessaire'
                ],
                'cost': 150.00
            },
            'brakes': {
                'description': 'Les freins approchent de leur limite d\'usure et doivent être inspectés.',
                'symptoms': [
                    'Bruit de grincement',
                    'Vibrations au freinage',
                    'Distance de freinage augmentée'
                ],
                'actions': [
                    'Inspection des plaquettes',
                    'Vérification des disques',
                    'Remplacement si nécessaire'
                ],
                'cost': 350.00
            },
            'tires': {
                'description': 'Les pneus montrent une usure importante et pourraient nécessiter un remplacement.',
                'symptoms': [
                    'Profondeur de sculpture faible',
                    'Usure irrégulière',
                    'Vibrations à haute vitesse'
                ],
                'actions': [
                    'Mesurer la profondeur de sculpture',
                    'Vérifier la pression',
                    'Remplacer si < 1.6mm'
                ],
                'cost': 400.00
            },
            'engine': {
                'description': 'Le moteur présente des signes d\'usure qui pourraient nécessiter une révision majeure.',
                'symptoms': [
                    'Consommation d\'huile excessive',
                    'Perte de puissance',
                    'Bruits inhabituels',
                    'Fumée d\'échappement'
                ],
                'actions': [
                    'Diagnostic complet',
                    'Test de compression',
                    'Révision ou remplacement'
                ],
                'cost': 3500.00
            },
            'transmission': {
                'description': 'La transmission montre des signes de défaillance potentielle.',
                'symptoms': [
                    'Changements de vitesse difficiles',
                    'Glissements',
                    'Bruits anormaux',
                    'Fuites de fluide'
                ],
                'actions': [
                    'Vérifier le niveau de fluide',
                    'Diagnostic électronique',
                    'Révision ou remplacement'
                ],
                'cost': 2800.00
            },
            'alternator': {
                'description': 'L\'alternateur pourrait être défaillant, affectant la recharge de la batterie.',
                'symptoms': [
                    'Voyant batterie allumé',
                    'Lumières vacillantes',
                    'Batterie qui se décharge'
                ],
                'actions': [
                    'Tester la sortie de l\'alternateur',
                    'Vérifier la courroie',
                    'Remplacer si nécessaire'
                ],
                'cost': 450.00
            },
            'starter': {
                'description': 'Le démarreur montre des signes de faiblesse.',
                'symptoms': [
                    'Clic lors du démarrage',
                    'Démarrage lent',
                    'Nécessite plusieurs tentatives'
                ],
                'actions': [
                    'Tester le démarreur',
                    'Vérifier les connexions',
                    'Remplacer si défectueux'
                ],
                'cost': 350.00
            },
            'suspension': {
                'description': 'La suspension présente une usure qui affecte le confort et la sécurité.',
                'symptoms': [
                    'Conduite cahoteuse',
                    'Usure irrégulière des pneus',
                    'Bruits lors des bosses',
                    'Véhicule penche dans les virages'
                ],
                'actions': [
                    'Inspection complète de la suspension',
                    'Tester les amortisseurs',
                    'Remplacer les composants usés'
                ],
                'cost': 800.00
            },
            'cooling': {
                'description': 'Le système de refroidissement pourrait présenter des défaillances.',
                'symptoms': [
                    'Surchauffe du moteur',
                    'Fuites de liquide de refroidissement',
                    'Ventilateur ne fonctionne pas',
                    'Température fluctuante'
                ],
                'actions': [
                    'Vérifier le niveau de liquide',
                    'Tester le thermostat',
                    'Inspecter le radiateur',
                    'Réparer les fuites'
                ],
                'cost': 550.00
            },
        }
        
        return details_map.get(component, {
            'description': f'Le composant {component} nécessite une attention.',
            'symptoms': ['À surveiller'],
            'actions': ['Inspection recommandée'],
            'cost': 200.00
        })


class MaintenanceRecommender:
    """
    Génère des recommandations de maintenance basées sur ML
    """
    
    @classmethod
    def generate_recommendations(cls, vehicle):
        """
        Génère des recommandations de maintenance pour un véhicule
        
        Returns: List of MaintenanceRecommendation instances
        """
        recommendations = []
        
        # Get health score
        health_scores = vehicle.health_scores.all()[:1]
        if health_scores:
            health_score = health_scores[0]
            
            # Low health score triggers recommendations
            if health_score.score < 70:
                recommendations.extend(cls._health_based_recommendations(vehicle, health_score))
        
        # Get failure predictions
        predictions = vehicle.failure_predictions.filter(status='active')
        for prediction in predictions:
            rec = cls._prediction_based_recommendation(vehicle, prediction)
            if rec:
                recommendations.append(rec)
        
        # Mileage-based recommendations
        recommendations.extend(cls._mileage_based_recommendations(vehicle))
        
        return recommendations
    
    @classmethod
    def _health_based_recommendations(cls, vehicle, health_score):
        """Recommandations basées sur le score de santé"""
        recommendations = []
        
        if health_score.maintenance_factor < 60:
            rec = MaintenanceRecommendation.objects.create(
                vehicle=vehicle,
                title="Maintenance régulière requise",
                description="Votre véhicule manque de maintenance régulière. Une révision complète est recommandée.",
                priority='high',
                type='preventive',
                component='general',
                recommended_service='Révision complète',
                estimated_cost=300.00,
                estimated_duration_hours=3.0,
                recommended_by_date=date.today() + timedelta(days=30),
                confidence=0.85,
                based_on_factors=['low_maintenance_score', 'vehicle_age']
            )
            recommendations.append(rec)
        
        return recommendations
    
    @classmethod
    def _prediction_based_recommendation(cls, vehicle, prediction):
        """Recommandation basée sur une prédiction de panne"""
        if prediction.failure_probability < 0.6:
            return None
        
        priority_map = {
            'critical': 'urgent',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
        }
        
        rec = MaintenanceRecommendation.objects.create(
            vehicle=vehicle,
            failure_prediction=prediction,
            title=f"Prévention panne: {prediction.get_component_display()}",
            description=prediction.description,
            priority=priority_map[prediction.severity],
            type='predictive',
            component=prediction.component,
            recommended_service=f"Inspection et maintenance {prediction.get_component_display()}",
            estimated_cost=prediction.estimated_repair_cost,
            estimated_duration_hours=2.0,
            recommended_by_date=prediction.predicted_failure_date - timedelta(days=7) if prediction.predicted_failure_date else None,
            confidence=prediction.confidence,
            based_on_factors=['ml_prediction', f'probability_{int(prediction.failure_probability*100)}%']
        )
        
        return rec
    
    @classmethod
    def _mileage_based_recommendations(cls, vehicle):
        """Recommandations basées sur le kilométrage"""
        recommendations = []
        mileage = vehicle.current_mileage or 0
        
        # Oil change every 10,000 km
        if mileage % 10000 < 1000 and mileage > 0:
            rec = MaintenanceRecommendation.objects.create(
                vehicle=vehicle,
                title="Vidange moteur recommandée",
                description="Votre véhicule approche des 10,000 km depuis la dernière vidange probable.",
                priority='medium',
                type='preventive',
                component='engine',
                recommended_service='Vidange moteur + filtre',
                estimated_cost=80.00,
                estimated_duration_hours=0.5,
                recommended_by_mileage=((mileage // 10000) + 1) * 10000,
                confidence=0.90,
                based_on_factors=['mileage_interval']
            )
            recommendations.append(rec)
        
        return recommendations
