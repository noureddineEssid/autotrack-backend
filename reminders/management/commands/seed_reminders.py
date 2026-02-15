from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from reminders.models import Reminder
from users.models import User
from vehicles.models import Vehicle
from maintenances.models import Maintenance
from documents.models import Document
from diagnostics.models import Diagnostic


class Command(BaseCommand):
    help = 'Seeds the reminders table with realistic data'

    def handle(self, *args, **kwargs):
        Reminder.objects.all().delete()
        self.stdout.write('Reminders table cleared')

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
        maintenances = list(Maintenance.objects.all())
        documents = list(Document.objects.all())
        diagnostics = list(Diagnostic.objects.all())

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return

        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Please run seed_vehicles first.'))
            return

        self.stdout.write('\nCreating reminders...')
        created_reminders = []
        now = timezone.now()

        for user in users:
            user_vehicles = [v for v in vehicles if v.owner == user]
            vehicle = user_vehicles[0] if user_vehicles else vehicles[0]

            maintenance = next((m for m in maintenances if m.vehicle == vehicle), None)
            document = next((d for d in documents if d.vehicle == vehicle), None)
            diagnostic = next((d for d in diagnostics if d.vehicle == vehicle), None)

            created_reminders.append(
                Reminder.objects.create(
                    user=user,
                    reminder_type='maintenance',
                    title='Revision a planifier',
                    message='Une revision est recommandee dans les 30 prochains jours.',
                    priority='high',
                    vehicle=vehicle,
                    maintenance=maintenance,
                    remind_at=now + timedelta(days=10),
                    status='pending',
                )
            )

            if document:
                created_reminders.append(
                    Reminder.objects.create(
                        user=user,
                        reminder_type='document_expiry',
                        title='Assurance a renouveler',
                        message='Votre assurance arrive a echeance prochainement.',
                        priority='urgent',
                        vehicle=vehicle,
                        document=document,
                        remind_at=now + timedelta(days=20),
                        status='pending',
                    )
                )

            if diagnostic:
                created_reminders.append(
                    Reminder.objects.create(
                        user=user,
                        reminder_type='diagnostic_followup',
                        title='Suivi diagnostic',
                        message='Pensez a planifier un suivi avec votre garage.',
                        priority='medium',
                        vehicle=vehicle,
                        diagnostic=diagnostic,
                        remind_at=now - timedelta(days=2),
                        status='sent',
                        sent_at=now - timedelta(days=2),
                        read_at=now - timedelta(days=1),
                    )
                )

            created_reminders.append(
                Reminder.objects.create(
                    user=user,
                    reminder_type='custom',
                    title='Changement de pneus',
                    message='Pensez a verifier l\'usure des pneus avant l\'hiver.',
                    priority='medium',
                    vehicle=vehicle,
                    remind_at=now + timedelta(days=40),
                    status='pending',
                    repeat=True,
                    repeat_interval='yearly',
                )
            )

        self.stdout.write(f'  ✓ Created {len(created_reminders)} reminders')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {len(created_reminders)} reminders'))
