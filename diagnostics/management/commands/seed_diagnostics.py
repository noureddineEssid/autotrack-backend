from django.core.management.base import BaseCommand
from django.utils import timezone
from diagnostics.models import Diagnostic, DiagnosticReply
from vehicles.models import Vehicle
from users.models import User
from datetime import timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seeds the diagnostics and diagnostic replies tables'

    def handle(self, *args, **kwargs):
        # Nettoyer
        DiagnosticReply.objects.all().delete()
        Diagnostic.objects.all().delete()
        self.stdout.write('Tables cleared')
        
        now = timezone.now()
        
        # Récupérer véhicules et utilisateurs
        vehicles = list(Vehicle.objects.all()[:3])
        users = list(User.objects.all()[:3])
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Run seed_vehicles first.'))
            return
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Run seed_users first.'))
            return
        
        diagnostic_scenarios = [
            {
                'title': 'Bruit étrange au freinage',
                'description': 'J\'entends un bruit de grincement quand je freine, surtout à faible vitesse.',
                'ai_analysis': 'Le grincement au freinage est généralement causé par l\'usure des plaquettes de frein.',
                'confidence_score': Decimal('0.85'),
            },
            {
                'title': 'Voyant moteur allumé',
                'description': 'Le voyant "Check Engine" s\'est allumé ce matin.',
                'ai_analysis': 'Le voyant moteur peut indiquer divers problèmes. Diagnostic électronique recommandé.',
                'confidence_score': Decimal('0.70'),
            },
            {
                'title': 'Consommation excessive',
                'description': 'Ma consommation a augmenté de 20% ces dernières semaines.',
                'ai_analysis': 'Plusieurs causes possibles : pneus, filtres, injection. Contrôle général recommandé.',
                'confidence_score': Decimal('0.65'),
            },
            {
                'title': 'Problème de démarrage à froid',
                'description': 'Le matin, ma voiture a du mal à démarrer.',
                'ai_analysis': 'Difficultés au démarrage à froid : vérifiez la batterie et ses bornes.',
                'confidence_score': Decimal('0.80'),
            },
            {
                'title': 'Vibrations au volant',
                'description': 'À partir de 100 km/h, je ressens des vibrations dans le volant.',
                'ai_analysis': 'Vibrations à haute vitesse : déséquilibrage des roues probable.',
                'confidence_score': Decimal('0.90'),
            },
        ]
        
        diagnostics_created = []
        replies_created = []
        
        for i, scenario in enumerate(diagnostic_scenarios):
            vehicle = vehicles[i % len(vehicles)]
            user = users[i % len(users)]
            days_ago = random.randint(1, 60)
            created_date = now - timedelta(days=days_ago)
            
            diagnostic = Diagnostic.objects.create(
                user=user,
                vehicle=vehicle,
                title=scenario['title'],
                description=scenario['description'],
                status=random.choice(['pending', 'in_progress', 'completed']),
                ai_analysis=scenario['ai_analysis'],
                confidence_score=scenario['confidence_score'],
            )
            diagnostics_created.append(diagnostic)
            
            # Créer les réponses
            reply1 = DiagnosticReply.objects.create(
                diagnostic=diagnostic,
                sender=user,
                sender_type='user',
                message=scenario['description'],
                metadata={},
            )
            replies_created.append(reply1)
            
            reply2 = DiagnosticReply.objects.create(
                diagnostic=diagnostic,
                sender=None,
                sender_type='ai',
                message=scenario['ai_analysis'],
                metadata={'confidence': float(scenario['confidence_score'])},
            )
            replies_created.append(reply2)
            
            if random.random() > 0.5:
                reply3 = DiagnosticReply.objects.create(
                    diagnostic=diagnostic,
                    sender=user,
                    sender_type='user',
                    message='Merci pour cette analyse ! Je vais prendre rendez-vous au garage.',
                    metadata={},
                )
                replies_created.append(reply3)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(diagnostics_created)} diagnostics'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(replies_created)} replies'))
        
        stats = {}
        for status in ['pending', 'in_progress', 'completed']:
            count = Diagnostic.objects.filter(status=status).count()
            if count > 0:
                stats[status] = count
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'  - {len(diagnostics_created)} diagnostics')
        self.stdout.write(f'  - {len(replies_created)} replies')
        for status, count in stats.items():
            self.stdout.write(f'  - {count} {status}')
