from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import Notification
from users.models import User
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the notifications table'

    def handle(self, *args, **kwargs):
        Notification.objects.all().delete()
        self.stdout.write('Table cleared')
        
        now = timezone.now()
        users = list(User.objects.all()[:3])
        
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found.'))
            return
        
        notification_templates = [
            {'title': 'Bienvenue', 'message': 'Merci de nous avoir rejoint!', 'type': 'success', 'link': '/dashboard'},
            {'title': 'Révision à prévoir', 'message': 'Révision dans 2 semaines.', 'type': 'maintenance_reminder', 'link': '/maintenances'},
            {'title': 'Abonnement', 'message': 'Expire dans 7 jours.', 'type': 'subscription_expiring', 'link': '/subscriptions'},
        ]
        
        notifications_created = []
        for user in users:
            for i in range(random.randint(2, 4)):
                template = random.choice(notification_templates)
                is_read = random.choice([True, False])
                notif = Notification.objects.create(
                    user=user,
                    title=template['title'],
                    message=template['message'],
                    notification_type=template['type'],
                    is_read=is_read,
                    read_at=now if is_read else None,
                    link=template['link'],
                )
                notifications_created.append(notif)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(notifications_created)} notifications'))
