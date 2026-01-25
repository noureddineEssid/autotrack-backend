from django.core.management.base import BaseCommand
from plans.models import Plan, PlanFeature, PlanFeatureValue
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seeds the plans, plan features, and plan feature values tables'

    def handle(self, *args, **kwargs):
        # Nettoyer les tables
        PlanFeatureValue.objects.all().delete()
        Plan.objects.all().delete()
        PlanFeature.objects.all().delete()
        self.stdout.write('Tables cleared')
        
        # Créer les fonctionnalités
        features = [
            {'name': 'Max Vehicles', 'description': 'Maximum number of vehicles', 'feature_key': 'max_vehicles'},
            {'name': 'Storage', 'description': 'Storage space for documents', 'feature_key': 'storage'},
            {'name': 'Maintenances', 'description': 'Monthly maintenance records', 'feature_key': 'maintenances'},
            {'name': 'Diagnostics', 'description': 'AI diagnostics per month', 'feature_key': 'diagnostics'},
            {'name': 'AI Assistant', 'description': 'Access to AI assistant', 'feature_key': 'ai_assistant'},
            {'name': 'Support', 'description': 'Support level', 'feature_key': 'support'},
        ]
        
        created_features = []
        for feature_data in features:
            feature = PlanFeature.objects.create(**feature_data)
            created_features.append(feature)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(created_features)} features'))
        
        # Créer les plans
        plans_data = [
            {
                'name': 'Free',
                'description': 'Pour découvrir AutoTrack',
                'price': Decimal('0.00'),
                'currency': 'EUR',
                'interval': 'month',
                'is_popular': False,
                'is_active': True,
            },
            {
                'name': 'Standard',
                'description': 'Pour les conducteurs individuels',
                'price': Decimal('9.99'),
                'currency': 'EUR',
                'interval': 'month',
                'is_popular': True,
                'is_active': True,
            },
            {
                'name': 'Premium',
                'description': 'Pour les passionnés et professionnels',
                'price': Decimal('19.99'),
                'currency': 'EUR',
                'interval': 'month',
                'is_popular': False,
                'is_active': True,
            },
        ]
        
        created_plans = []
        for plan_data in plans_data:
            plan = Plan.objects.create(**plan_data)
            created_plans.append(plan)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(created_plans)} plans'))
        
        # Associer les features aux plans avec leurs valeurs
        feature_values = [
            # Plan Gratuit
            {'plan': created_plans[0], 'feature': created_features[0], 'value': '2'},
            {'plan': created_plans[0], 'feature': created_features[1], 'value': '100 Mo'},
            {'plan': created_plans[0], 'feature': created_features[2], 'value': '10'},
            {'plan': created_plans[0], 'feature': created_features[3], 'value': '5'},
            {'plan': created_plans[0], 'feature': created_features[5], 'value': 'Communauté'},
            
            # Plan Standard
            {'plan': created_plans[1], 'feature': created_features[0], 'value': '10'},
            {'plan': created_plans[1], 'feature': created_features[1], 'value': '5 Go'},
            {'plan': created_plans[1], 'feature': created_features[2], 'value': '50'},
            {'plan': created_plans[1], 'feature': created_features[3], 'value': '30'},
            {'plan': created_plans[1], 'feature': created_features[4], 'value': 'true'},
            {'plan': created_plans[1], 'feature': created_features[5], 'value': 'Email'},
            
            # Plan Premium
            {'plan': created_plans[2], 'feature': created_features[0], 'value': 'Illimité'},
            {'plan': created_plans[2], 'feature': created_features[1], 'value': '50 Go'},
            {'plan': created_plans[2], 'feature': created_features[2], 'value': 'Illimité'},
            {'plan': created_plans[2], 'feature': created_features[3], 'value': 'Illimité'},
            {'plan': created_plans[2], 'feature': created_features[4], 'value': 'true'},
            {'plan': created_plans[2], 'feature': created_features[5], 'value': 'Prioritaire 24/7'},
        ]
        
        created_values = []
        for value_data in feature_values:
            value = PlanFeatureValue.objects.create(**value_data)
            created_values.append(value)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(created_values)} plan feature values'))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'  - {len(created_features)} features created')
        self.stdout.write(f'  - {len(created_plans)} plans created')
        self.stdout.write(f'  - {len(created_values)} values created')
