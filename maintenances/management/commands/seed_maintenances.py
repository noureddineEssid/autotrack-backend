from django.core.management.base import BaseCommand
from django.utils import timezone
from maintenances.models import Maintenance
from vehicles.models import Vehicle
from users.models import User
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the maintenances table'

    def handle(self, *args, **kwargs):
        # Nettoyer
        Maintenance.objects.all().delete()
        self.stdout.write('Table cleared')
        
        now = timezone.now()
        
        # Récupérer véhicules et utilisateurs
        vehicles = list(Vehicle.objects.all()[:2])
        users = list(User.objects.all()[:4])
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Run seed_vehicles first.'))
            return
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Run seed_users first.'))
            return
        
        service_types = [
            'Vidange moteur',
            'Changement filtres',
            'Contrôle freins',
            'Pneumatiques',
            'Révision complète',
            'Diagnostic électronique',
        ]
        
        maintenances = []
        for i, vehicle in enumerate(vehicles):
            num_maintenances = random.randint(3, 5)
            
            for j in range(num_maintenances):
                days_ago = random.randint(30, 365)
                service_date = now - timedelta(days=days_ago)
                
                maintenance = Maintenance.objects.create(
                    vehicle=vehicle,
                    created_by=users[i % len(users)],
                    performed_by=users[(i + 1) % len(users)] if random.random() > 0.3 else None,
                    service_date=service_date,
                    service_type=random.choice(service_types),
                    description=f'Entretien régulier du véhicule {vehicle.make} {vehicle.model}',
                    mileage=10000 + (days_ago * 30),
                    cost=round(random.uniform(50, 500), 2),
                    status=random.choice(['COMPLETED', 'SCHEDULED', 'IN_PROGRESS']),
                    invoice_url=f'https://example.com/invoices/inv_{i}_{j}.pdf' if random.random() > 0.5 else None,
                    reminder_sent=random.choice([True, False]),
                )
                maintenances.append(maintenance)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(maintenances)} maintenances'))
        
        stats = {}
        for status in ['COMPLETED', 'SCHEDULED', 'IN_PROGRESS', 'CANCELLED']:
            count = Maintenance.objects.filter(status=status).count()
            if count > 0:
                stats[status] = count
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'  - {len(maintenances)} total maintenances')
        for status, count in stats.items():
            self.stdout.write(f'  - {count} {status.lower()}')
