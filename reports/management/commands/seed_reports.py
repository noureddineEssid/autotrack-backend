from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.models import Report
from users.models import User
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = 'Seeds the reports table with realistic data'

    def handle(self, *args, **kwargs):
        Report.objects.all().delete()
        self.stdout.write('Reports table cleared')

        users = list(
            User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )
        vehicles = list(Vehicle.objects.all())

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return

        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Please run seed_vehicles first.'))
            return

        report_types = [
            'vehicle_summary',
            'maintenance_history',
            'diagnostic_history',
            'cost_analysis',
            'fuel_consumption',
        ]
        formats = ['pdf', 'excel']

        self.stdout.write('\nCreating reports...')
        created_reports = []

        for user in users:
            user_vehicles = [v for v in vehicles if v.owner == user]
            vehicle = user_vehicles[0] if user_vehicles else None

            for i in range(3):
                report_type = report_types[i % len(report_types)]
                format_choice = formats[i % len(formats)]
                status = 'completed' if i != 2 else 'pending'

                now = timezone.now()
                date_to = now.date()
                date_from = date_to - timedelta(days=120)

                report = Report.objects.create(
                    user=user,
                    report_type=report_type,
                    format=format_choice,
                    vehicle=vehicle,
                    date_from=date_from,
                    date_to=date_to,
                    include_charts=True,
                    include_images=False,
                    include_summary=True,
                    include_details=True,
                    status=status,
                    file_path=f'/media/reports/{user.id}/{report_type}_{i}.{format_choice}' if status == 'completed' else '',
                    file_size=350000 if status == 'completed' else None,
                    error_message='Generation en attente de donnees' if status == 'pending' else '',
                )
                created_reports.append(report)

        self.stdout.write(f'  ✓ Created {len(created_reports)} reports')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {len(created_reports)} reports'))
