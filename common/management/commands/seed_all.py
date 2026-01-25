from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seeds all collections with test data'

    def handle(self, *args, **kwargs):
        seeds = [
            ('seed_users', 'Users'),
            ('seed_vehicles', 'Vehicles'),
            ('seed_plans', 'Plans & Features'),
            ('seed_subscriptions', 'Subscriptions'),
            ('seed_garages', 'Garages'),
            ('seed_maintenances', 'Maintenances'),
            ('seed_diagnostics', 'Diagnostics'),
            ('seed_documents', 'Documents'),
            ('seed_bookings', 'Bookings'),
            ('seed_notifications', 'Notifications'),
            ('seed_reminders', 'Reminders'),
            ('seed_reports', 'Reports'),
            ('seed_ai_assistant', 'AI Assistant'),
            ('seed_ml_predictions', 'ML Predictions'),
            ('seed_stats', 'Statistics Cache'),
            ('seed_webhooks', 'Webhooks'),
            ('seed_settings', 'Settings'),
        ]
        
        self.stdout.write('🌱 Starting all seeds...\n')
        
        for command, name in seeds:
            try:
                self.stdout.write(f'📦 Running {name} seed...')
                call_command(command)
                self.stdout.write(self.style.SUCCESS(f'✅ {name} seed completed\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error running {name} seed: {str(e)}'))
                return
        
        self.stdout.write(self.style.SUCCESS('🎉 All seeds completed successfully!'))
