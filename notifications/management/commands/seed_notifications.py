from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import Notification
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the notifications table'

    def handle(self, *args, **kwargs):
        Notification.objects.all().delete()
        self.stdout.write('Table cleared')

        now = timezone.now()
        users = list(
            User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found.'))
            return

        notifications_created = []
        for user in users:
            notifications_created.append(
                Notification.objects.create(
                    user=user,
                    title='Bienvenue sur AutoTrack+',
                    message='Votre compte est actif. Ajoutez votre premier vehicule pour demarrer.',
                    notification_type='success',
                    is_read=True,
                    read_at=now,
                    link='/dashboard',
                )
            )
            notifications_created.append(
                Notification.objects.create(
                    user=user,
                    title='Revision a prevoir',
                    message='Une revision est recommandee dans les 30 prochains jours.',
                    notification_type='maintenance_reminder',
                    is_read=False,
                    link='/maintenances',
                )
            )
            notifications_created.append(
                Notification.objects.create(
                    user=user,
                    title='Abonnement actif',
                    message='Votre abonnement est en cours. Consultez les limites de votre plan.',
                    notification_type='info',
                    is_read=False,
                    link='/subscriptions',
                )
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(notifications_created)} notifications'))
