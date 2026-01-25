from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from reminders.models import Reminder
from users.models import User
from vehicles.models import Vehicle
from maintenances.models import Maintenance
from documents.models import Document
from diagnostics.models import Diagnostic
import random


class Command(BaseCommand):
    help = 'Seeds the reminders table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les rappels existants
        Reminder.objects.all().delete()
        self.stdout.write('Reminders table cleared')
        
        users = list(User.objects.all())
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
        
        # Créer les rappels
        self.stdout.write('\nCreating reminders...')
        created_reminders = []
        now = timezone.now()
        
        reminder_templates = [
            {
                'type': 'maintenance',
                'title': 'Révision à effectuer',
                'message': 'La révision de votre véhicule est prévue dans 7 jours.',
                'priority': 'high',
            },
            {
                'type': 'maintenance',
                'title': 'Vidange recommandée',
                'message': 'Il est temps de faire la vidange de votre véhicule.',
                'priority': 'medium',
            },
            {
                'type': 'document_expiry',
                'title': 'Assurance à renouveler',
                'message': 'Votre assurance automobile expire bientôt.',
                'priority': 'urgent',
            },
            {
                'type': 'document_expiry',
                'title': 'Contrôle technique à prévoir',
                'message': 'Le contrôle technique de votre véhicule arrive à échéance.',
                'priority': 'high',
            },
            {
                'type': 'diagnostic_followup',
                'title': 'Suivi diagnostic',
                'message': 'Un suivi est nécessaire suite au diagnostic précédent.',
                'priority': 'medium',
            },
            {
                'type': 'custom',
                'title': 'Changement de pneus',
                'message': 'N\'oubliez pas de changer vos pneus pour l\'hiver.',
                'priority': 'medium',
            },
        ]
        
        for i in range(25):  # Créer 25 rappels
            user = random.choice(users)
            vehicle = random.choice([v for v in vehicles if v.owner == user] or vehicles)
            template = random.choice(reminder_templates)
            
            # Date de rappel entre -5 et +30 jours
            remind_at = now + timedelta(days=random.randint(-5, 30))
            
            # Déterminer le statut basé sur la date
            if remind_at < now:
                status = random.choice(['sent', 'read', 'dismissed', 'completed'])
            else:
                status = 'pending'
            
            # Associer des objets liés selon le type
            maintenance = None
            document = None
            diagnostic = None
            
            if template['type'] == 'maintenance' and maintenances:
                maintenance = random.choice([m for m in maintenances if m.vehicle == vehicle] or maintenances)
            elif template['type'] == 'document_expiry' and documents:
                document = random.choice([d for d in documents if d.vehicle == vehicle] or documents)
            elif template['type'] == 'diagnostic_followup' and diagnostics:
                diagnostic = random.choice([d for d in diagnostics if d.vehicle == vehicle] or diagnostics)
            
            reminder = Reminder.objects.create(
                user=user,
                reminder_type=template['type'],
                title=template['title'],
                message=template['message'],
                priority=template['priority'],
                vehicle=vehicle,
                maintenance=maintenance,
                document=document,
                diagnostic=diagnostic,
                remind_at=remind_at,
                repeat=random.random() > 0.8,  # 20% de répétition
                repeat_interval=random.choice(['weekly', 'monthly', 'yearly']) if random.random() > 0.8 else '',
                status=status,
                sent_at=remind_at if status in ['sent', 'read', 'dismissed', 'completed'] else None,
                read_at=remind_at + timedelta(hours=random.randint(1, 24)) if status in ['read', 'dismissed', 'completed'] else None,
                dismissed_at=remind_at + timedelta(days=random.randint(1, 5)) if status == 'dismissed' else None,
            )
            created_reminders.append(reminder)
        
        self.stdout.write(f'  ✓ Created {len(created_reminders)} reminders')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {len(created_reminders)} reminders'))
