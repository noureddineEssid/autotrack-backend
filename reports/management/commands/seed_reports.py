from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from reports.models import Report
from users.models import User
from vehicles.models import Vehicle
import random


class Command(BaseCommand):
    help = 'Seeds the reports table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les rapports existants
        Report.objects.all().delete()
        self.stdout.write('Reports table cleared')
        
        users = list(User.objects.all())
        vehicles = list(Vehicle.objects.all())
        
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Please run seed_vehicles first.'))
            return
        
        # Types de rapports
        report_types = [
            'vehicle_summary',
            'maintenance_history',
            'diagnostic_history',
            'cost_analysis',
            'fuel_consumption',
            'comprehensive',
        ]
        
        formats = ['pdf', 'excel', 'csv']
        statuses = ['completed', 'completed', 'completed', 'pending', 'failed']  # Majorité completed
        
        # Créer les rapports
        self.stdout.write('\nCreating reports...')
        created_reports = []
        
        for i in range(20):  # Créer 20 rapports
            user = random.choice(users)
            vehicle = random.choice([v for v in vehicles if v.owner == user] or vehicles)
            report_type = random.choice(report_types)
            format_choice = random.choice(formats)
            status = random.choice(statuses)
            
            # Dates aléatoires pour les filtres
            now = timezone.now()
            date_to = now.date()
            date_from = date_to - timedelta(days=random.randint(30, 365))
            
            report = Report.objects.create(
                user=user,
                report_type=report_type,
                format=format_choice,
                vehicle=vehicle if random.random() > 0.3 else None,  # 70% avec véhicule spécifique
                date_from=date_from if random.random() > 0.4 else None,
                date_to=date_to if random.random() > 0.4 else None,
                include_charts=random.random() > 0.2,
                include_images=random.random() > 0.3,
                include_summary=random.random() > 0.1,
                include_details=random.random() > 0.2,
                status=status,
                file_path=f'/media/reports/{user.id}/{report_type}_{i}.{format_choice}' if status == 'completed' else '',
                file_size=random.randint(50000, 5000000) if status == 'completed' else None,
                error_message='Generation failed due to insufficient data' if status == 'failed' else '',
            )
            created_reports.append(report)
        
        self.stdout.write(f'  ✓ Created {len(created_reports)} reports')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {len(created_reports)} reports'))
