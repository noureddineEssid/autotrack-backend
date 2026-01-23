"""
Celery tasks for ML predictions
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

from .models import FailurePrediction, MaintenanceRecommendation
from .ml_engine import VehicleHealthPredictor, FailurePredictor, MaintenanceRecommender


@shared_task
def calculate_vehicle_health_scores():
    """
    Calcule les scores de santé pour tous les véhicules (tâche quotidienne)
    """
    from vehicles.models import Vehicle
    
    vehicles = Vehicle.objects.all()
    count = 0
    
    for vehicle in vehicles:
        try:
            VehicleHealthPredictor.calculate_health_score(vehicle)
            count += 1
        except Exception as e:
            print(f"Error calculating health for vehicle {vehicle.id}: {e}")
    
    return f"Calculated health scores for {count} vehicles"


@shared_task
def generate_failure_predictions():
    """
    Génère des prédictions de pannes pour tous les véhicules (tâche quotidienne)
    """
    from vehicles.models import Vehicle
    
    vehicles = Vehicle.objects.all()
    total_predictions = 0
    
    for vehicle in vehicles:
        try:
            predictions = FailurePredictor.predict_failures(vehicle)
            total_predictions += len(predictions)
        except Exception as e:
            print(f"Error predicting failures for vehicle {vehicle.id}: {e}")
    
    return f"Generated {total_predictions} failure predictions"


@shared_task
def generate_maintenance_recommendations():
    """
    Génère des recommandations de maintenance (tâche hebdomadaire)
    """
    from vehicles.models import Vehicle
    
    vehicles = Vehicle.objects.all()
    total_recommendations = 0
    
    for vehicle in vehicles:
        try:
            recommendations = MaintenanceRecommender.generate_recommendations(vehicle)
            total_recommendations += len(recommendations)
        except Exception as e:
            print(f"Error generating recommendations for vehicle {vehicle.id}: {e}")
    
    return f"Generated {total_recommendations} maintenance recommendations"


@shared_task
def send_urgent_prediction_alerts():
    """
    Envoie des alertes email pour les prédictions urgentes (tâche quotidienne)
    """
    urgent_predictions = FailurePrediction.objects.filter(
        status='active'
    ).filter(
        models.Q(severity='critical') | 
        (models.Q(failure_probability__gte=0.8) & models.Q(estimated_days_until_failure__lte=30))
    )
    
    emails_sent = 0
    
    for prediction in urgent_predictions:
        try:
            user = prediction.vehicle.user
            if not user.email:
                continue
            
            subject = f"⚠️ Alerte Panne Urgente - {prediction.get_component_display()}"
            message = f"""
Bonjour {user.first_name or user.username},

Une panne URGENTE a été détectée pour votre véhicule {prediction.vehicle}:

🚗 Véhicule: {prediction.vehicle.make} {prediction.vehicle.model} ({prediction.vehicle.license_plate})
⚙️ Composant: {prediction.get_component_display()}
📊 Probabilité de panne: {prediction.failure_probability:.0%}
🔴 Sévérité: {prediction.get_severity_display()}
📅 Panne estimée dans: {prediction.estimated_days_until_failure} jours

Description:
{prediction.description}

Symptômes à surveiller:
{chr(10).join('- ' + symptom for symptom in prediction.symptoms)}

Actions recommandées:
{chr(10).join('- ' + action for action in prediction.recommended_actions)}

💰 Coût estimé: {prediction.estimated_repair_cost}€

Nous vous recommandons de prendre rendez-vous avec un garage rapidement.

Cordialement,
L'équipe AutoTrack
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            emails_sent += 1
            
        except Exception as e:
            print(f"Error sending alert for prediction {prediction.id}: {e}")
    
    return f"Sent {emails_sent} urgent prediction alerts"


@shared_task
def send_maintenance_reminders():
    """
    Envoie des rappels pour les recommandations de maintenance urgentes
    """
    urgent_recommendations = MaintenanceRecommendation.objects.filter(
        priority='urgent',
        is_completed=False,
        dismissed=False
    )
    
    emails_sent = 0
    
    for recommendation in urgent_recommendations:
        try:
            user = recommendation.vehicle.user
            if not user.email:
                continue
            
            subject = f"🔧 Maintenance Urgente Recommandée - {recommendation.vehicle}"
            message = f"""
Bonjour {user.first_name or user.username},

Une maintenance URGENTE est recommandée pour votre véhicule:

🚗 Véhicule: {recommendation.vehicle}
🔧 Service: {recommendation.recommended_service}
⚠️ Priorité: {recommendation.get_priority_display()}
📝 Type: {recommendation.get_type_display()}

Description:
{recommendation.description}

💰 Coût estimé: {recommendation.estimated_cost}€
⏱️ Durée estimée: {recommendation.estimated_duration_hours}h

{f'📅 Recommandé avant le: {recommendation.recommended_by_date}' if recommendation.recommended_by_date else ''}
{f'📏 Recommandé avant: {recommendation.recommended_by_mileage} km' if recommendation.recommended_by_mileage else ''}

Prenez rendez-vous dès maintenant pour éviter des problèmes plus graves.

Cordialement,
L'équipe AutoTrack
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            emails_sent += 1
            
        except Exception as e:
            print(f"Error sending reminder for recommendation {recommendation.id}: {e}")
    
    return f"Sent {emails_sent} maintenance reminders"


@shared_task
def cleanup_old_predictions():
    """
    Archive les anciennes prédictions résolues (> 6 mois)
    """
    six_months_ago = timezone.now() - timedelta(days=180)
    
    old_predictions = FailurePrediction.objects.filter(
        resolved_at__lt=six_months_ago
    )
    
    count = old_predictions.count()
    # In production, move to archive instead of delete
    # old_predictions.delete()
    
    return f"Found {count} old predictions to archive"
