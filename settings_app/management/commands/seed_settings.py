from django.core.management.base import BaseCommand
from settings_app.models import UserSettings
from users.models import User
import random


class Command(BaseCommand):
    help = 'Seeds the user settings table'

    def handle(self, *args, **kwargs):
        UserSettings.objects.all().delete()
        self.stdout.write('Table cleared')
        
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found.'))
            return
        
        for user in users:
            UserSettings.objects.create(
                user=user,
                language=random.choice(['en', 'fr', 'es']),
                theme=random.choice(['light', 'dark', 'auto']),
                timezone='Europe/Paris',
                email_notifications=True,
                push_notifications=True,
                maintenance_reminders=True,
                subscription_alerts=True,
                profile_public=False,
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(users)} user settings'))
