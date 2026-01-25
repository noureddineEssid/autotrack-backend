from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from ml_predictions.models import VehicleHealthScore, FailurePrediction, MaintenanceRecommendation
from vehicles.models import Vehicle
import random


class Command(BaseCommand):
    help = 'Seeds the ML predictions tables with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les prédictions existantes
        VehicleHealthScore.objects.all().delete()
        FailurePrediction.objects.all().delete()
        MaintenanceRecommendation.objects.all().delete()
        self.stdout.write('ML Predictions tables cleared')
        
        vehicles = list(Vehicle.objects.all())
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Please run seed_vehicles first.'))
            return
        
        # Créer les scores de santé
        self.stdout.write('\nCreating vehicle health scores...')
        health_scores_created = 0
        
        for vehicle in vehicles:
            # Créer 3-5 scores historiques
            for i in range(random.randint(3, 5)):
                score = random.uniform(65, 95)
                
                VehicleHealthScore.objects.create(
                    vehicle=vehicle,
                    score=score,
                    age_factor=random.uniform(0.7, 1.0),
                    mileage_factor=random.uniform(0.6, 1.0),
                    maintenance_factor=random.uniform(0.7, 1.0),
                    repair_history_factor=random.uniform(0.8, 1.0),
                    usage_pattern_factor=random.uniform(0.7, 1.0),
                    model_version='v1.2.3',
                    confidence=random.uniform(0.75, 0.95),
                )
                health_scores_created += 1
        
        self.stdout.write(f'  ✓ Created {health_scores_created} health scores')
        
        # Créer les prédictions de panne
        self.stdout.write('\nCreating failure predictions...')
        failure_predictions_created = 0
        
        components = [
            ('engine', 'Moteur'),
            ('brakes', 'Freins'),
            ('battery', 'Batterie'),
            ('alternator', 'Alternateur'),
            ('suspension', 'Suspension'),
            ('transmission', 'Transmission'),
        ]
        
        severities = ['critical', 'high', 'medium', 'low']
        
        for vehicle in vehicles[:len(vehicles)//2]:  # Pour la moitié des véhicules
            num_predictions = random.randint(1, 3)
            
            for i in range(num_predictions):
                component, component_name = random.choice(components)
                severity = random.choice(severities)
                probability = random.uniform(0.3, 0.9)
                days_until = random.randint(15, 180)
                
                symptoms = []
                actions = []
                
                if component == 'engine':
                    symptoms = ['Bruit anormal au ralenti', 'Perte de puissance', 'Fumée à l\'échappement']
                    actions = ['Vérifier le niveau d\'huile', 'Faire un diagnostic moteur', 'Révision complète recommandée']
                elif component == 'brakes':
                    symptoms = ['Bruit de grincement au freinage', 'Pédale de frein molle', 'Distance de freinage augmentée']
                    actions = ['Vérifier l\'épaisseur des plaquettes', 'Contrôler le liquide de frein', 'Remplacer les plaquettes si nécessaire']
                elif component == 'battery':
                    symptoms = ['Démarrage difficile', 'Voyants qui clignotent', 'Accessoires électriques faibles']
                    actions = ['Tester la batterie', 'Vérifier l\'alternateur', 'Remplacer la batterie si >4 ans']
                
                FailurePrediction.objects.create(
                    vehicle=vehicle,
                    component=component,
                    severity=severity,
                    status=random.choice(['active', 'acknowledged']),
                    failure_probability=probability,
                    predicted_failure_date=date.today() + timedelta(days=days_until),
                    estimated_days_until_failure=days_until,
                    confidence=random.uniform(0.7, 0.95),
                    current_mileage=random.randint(50000, 200000),
                    vehicle_age_years=date.today().year - vehicle.year,
                    description=f'Risque de panne du {component_name} détecté par analyse prédictive',
                    symptoms=symptoms[:random.randint(1, len(symptoms))] if symptoms else [],
                    recommended_actions=actions[:random.randint(1, len(actions))] if actions else [],
                    estimated_repair_cost=random.uniform(200, 1500),
                    model_version='v1.2.3',
                    feature_importance={
                        'mileage': round(random.uniform(0.2, 0.4), 2),
                        'age': round(random.uniform(0.15, 0.3), 2),
                        'maintenance_history': round(random.uniform(0.2, 0.35), 2),
                    }
                )
                failure_predictions_created += 1
        
        self.stdout.write(f'  ✓ Created {failure_predictions_created} failure predictions')
        
        # Créer les recommandations de maintenance
        self.stdout.write('\nCreating maintenance recommendations...')
        recommendations_created = 0
        
        for vehicle in vehicles:
            num_recommendations = random.randint(1, 3)
            
            for i in range(num_recommendations):
                priority = random.choice(['low', 'medium', 'high', 'urgent'])
                rec_type = random.choice(['preventive', 'corrective', 'urgent'])
                
                MaintenanceRecommendation.objects.create(
                    vehicle=vehicle,
                    title=f'Recommandation de maintenance pour {vehicle}',
                    description='Maintenance recommandée suite à l\'analyse prédictive',
                    priority=priority,
                    type=rec_type,
                    component=random.choice(['Moteur', 'Freins', 'Suspension', 'Batterie']),
                    recommended_service=random.choice(['Révision', 'Remplacement', 'Contrôle', 'Nettoyage']),
                    estimated_cost=random.uniform(100, 800),
                    estimated_duration_hours=random.uniform(1, 4),
                    recommended_by_date=date.today() + timedelta(days=random.randint(30, 180)),
                    confidence=random.uniform(0.7, 0.95),
                    based_on_factors=['Kilométrage élevé', 'Âge du véhicule', 'Historique d\'entretien'][:random.randint(1, 3)],
                )
                recommendations_created += 1
        
        self.stdout.write(f'  ✓ Created {recommendations_created} maintenance recommendations')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created ML predictions:'))
        self.stdout.write(f'   • {health_scores_created} health scores')
        self.stdout.write(f'   • {failure_predictions_created} failure predictions')
        self.stdout.write(f'   • {recommendations_created} maintenance recommendations')
