from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from maintenances.models import Maintenance
from vehicles.models import Vehicle
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the maintenances table'

    def handle(self, *args, **kwargs):
        Maintenance.objects.all().delete()
        self.stdout.write('Table cleared')

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
            'amal.benali@example.com': 4,     # free (<= 10)
            'youssef.chaari@example.com': 12,  # standard (<= 50)
            'salma.trabelsi@example.com': 25,  # premium (<= 200)
        }

        service_types = [
            'Vidange moteur',
            'Changement filtres',
            'Controle freins',
            'Pneumatiques',
            'Revision complete',
            'Diagnostic electronique',
        ]

        maintenances = []

        for email, user in users.items():
            vehicles = vehicles_by_user.get(email, [])
            if not vehicles:
                continue

            # Current month maintenances (respect plan limits)
            for i in range(monthly_targets[email]):
                vehicle = vehicles[i % len(vehicles)]
                service_date = now - timedelta(days=(i % 20))
                maintenance = Maintenance.objects.create(
                    vehicle=vehicle,
                    created_by=user,
                    performed_by=user,
                    service_date=service_date,
                    service_type=service_types[i % len(service_types)],
                    description=f'Entretien planifie pour {vehicle.make} {vehicle.model}',
                    mileage=20000 + (i * 450),
                    cost=150 + (i % 5) * 25,
                    status='COMPLETED' if i % 3 != 0 else 'IN_PROGRESS',
                    invoice_url=f'https://example.com/invoices/{vehicle.license_plate}_{i}.pdf',
                    reminder_sent=True,
                )
                maintenances.append(maintenance)

            # Past maintenances (history)
            for i in range(3):
                vehicle = vehicles[(i + 1) % len(vehicles)]
                service_date = now - timedelta(days=60 + (i * 30))
                maintenance = Maintenance.objects.create(
                    vehicle=vehicle,
                    created_by=user,
                    performed_by=user,
                    service_date=service_date,
                    service_type=service_types[(i + 2) % len(service_types)],
                    description=f'Historique entretien pour {vehicle.make} {vehicle.model}',
                    mileage=12000 + (i * 3000),
                    cost=210 + (i * 35),
                    status='COMPLETED',
                    invoice_url=f'https://example.com/invoices/{vehicle.license_plate}_hist_{i}.pdf',
                    reminder_sent=True,
                )
                maintenances.append(maintenance)

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(maintenances)} maintenances'))

        stats = {}
        for status in ['COMPLETED', 'SCHEDULED', 'IN_PROGRESS', 'CANCELLED']:
            count = Maintenance.objects.filter(status=status).count()
            if count > 0:
                stats[status] = count

        self.stdout.write('\n📊 Summary:')
        self.stdout.write(f'  - {len(maintenances)} total maintenances')
        for status, count in stats.items():
            self.stdout.write(f'  - {count} {status.lower()}')
