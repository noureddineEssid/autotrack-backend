from django.core.management.base import BaseCommand
from settings_app.models import UserSettings
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the user settings table'

    def handle(self, *args, **kwargs):
        UserSettings.objects.all().delete()
        self.stdout.write('Table cleared')

        users = list(
            User.objects.filter(
                email__in=[
                    'admin@autotrack.tn',
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found.'))
            return

        settings_by_email = {
            'admin@autotrack.tn': {'language': 'fr', 'theme': 'dark'},
            'amal.benali@example.com': {'language': 'fr', 'theme': 'light'},
            'youssef.chaari@example.com': {'language': 'fr', 'theme': 'auto'},
            'salma.trabelsi@example.com': {'language': 'fr', 'theme': 'dark'},
        }

        for user in users:
            prefs = settings_by_email.get(user.email, {'language': 'fr', 'theme': 'auto'})
            UserSettings.objects.create(
                user=user,
                language=prefs['language'],
                theme=prefs['theme'],
                timezone='Africa/Tunis',
                email_notifications=True,
                push_notifications=True,
                maintenance_reminders=True,
                subscription_alerts=True,
                profile_public=False,
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(users)} user settings'))
