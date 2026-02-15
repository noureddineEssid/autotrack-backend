from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from diagnostics.models import Diagnostic, DiagnosticReply
from vehicles.models import Vehicle
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the diagnostics and diagnostic replies tables'

    def handle(self, *args, **kwargs):
        DiagnosticReply.objects.all().delete()
        Diagnostic.objects.all().delete()
        self.stdout.write('Tables cleared')

        now = timezone.now()

        users = {
            user.email: user
            for user in User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        }

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Run seed_users first.'))
            return

        vehicles_by_user = {
            email: list(Vehicle.objects.filter(owner=user))
            for email, user in users.items()
        }

        if not any(vehicles_by_user.values()):
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Run seed_vehicles first.'))
            return

        monthly_targets = {
            'amal.benali@example.com': 3,      # free (<= 5)
            'youssef.chaari@example.com': 10,  # standard (<= 30)
            'salma.trabelsi@example.com': 20,  # premium (unlimited)
        }

        diagnostic_scenarios = [
            {
                'title': 'Bruit etrange au freinage',
                'description': 'J\'entends un grincement quand je freine a faible vitesse.',
                'ai_analysis': 'Usure probable des plaquettes de frein avant.',
                'confidence_score': Decimal('0.85'),
            },
            {
                'title': 'Voyant moteur allume',
                'description': 'Le voyant Check Engine s\'est allume ce matin.',
                'ai_analysis': 'Un diagnostic electronique est recommande pour isoler la cause.',
                'confidence_score': Decimal('0.70'),
            },
            {
                'title': 'Consommation excessive',
                'description': 'Ma consommation a augmente de 20% ces dernieres semaines.',
                'ai_analysis': 'Verifier pression des pneus et filtres. Controle injection conseille.',
                'confidence_score': Decimal('0.65'),
            },
            {
                'title': 'Probleme de demarrage a froid',
                'description': 'Le matin, la voiture demarre difficilement.',
                'ai_analysis': 'Verifier batterie et systeme de charge.',
                'confidence_score': Decimal('0.80'),
            },
            {
                'title': 'Vibrations au volant',
                'description': 'Des vibrations apparaissent a partir de 100 km/h.',
                'ai_analysis': 'Probable desequilibrage des roues.',
                'confidence_score': Decimal('0.90'),
            },
        ]

        diagnostics_created = []
        replies_created = []

        for email, user in users.items():
            vehicles = vehicles_by_user.get(email, [])
            if not vehicles:
                continue

            for i in range(monthly_targets[email]):
                scenario = diagnostic_scenarios[i % len(diagnostic_scenarios)]
                vehicle = vehicles[i % len(vehicles)]
                created_date = now - timedelta(days=(i % 25))

                diagnostic = Diagnostic.objects.create(
                    user=user,
                    vehicle=vehicle,
                    title=scenario['title'],
                    description=scenario['description'],
                    status='completed' if i % 3 == 0 else 'in_progress',
                    ai_analysis=scenario['ai_analysis'],
                    confidence_score=scenario['confidence_score'],
                )
                Diagnostic.objects.filter(id=diagnostic.id).update(created_at=created_date)
                diagnostics_created.append(diagnostic)

                replies_created.append(
                    DiagnosticReply.objects.create(
                        diagnostic=diagnostic,
                        sender=user,
                        sender_type='user',
                        message=scenario['description'],
                        metadata={},
                    )
                )
                replies_created.append(
                    DiagnosticReply.objects.create(
                        diagnostic=diagnostic,
                        sender=None,
                        sender_type='ai',
                        message=scenario['ai_analysis'],
                        metadata={'confidence': float(scenario['confidence_score'])},
                    )
                )

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(diagnostics_created)} diagnostics'))
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(replies_created)} replies'))

        stats = {}
        for status in ['pending', 'in_progress', 'completed']:
            count = Diagnostic.objects.filter(status=status).count()
            if count > 0:
                stats[status] = count

        self.stdout.write('\n📊 Summary:')
        self.stdout.write(f'  - {len(diagnostics_created)} diagnostics')
        self.stdout.write(f'  - {len(replies_created)} replies')
        for status, count in stats.items():
            self.stdout.write(f'  - {count} {status}')
