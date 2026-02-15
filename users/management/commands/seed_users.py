from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the users table with realistic data'

    def handle(self, *args, **kwargs):
        User.objects.all().delete()
        self.stdout.write('Users table cleared')

        default_password = 'AutoTrack2025!'

        admin_data = {
            'email': 'admin@autotrack.tn',
            'first_name': 'Nabil',
            'last_name': 'Kharroubi',
            'phone_number': '+21620123456',
            'roles': ['admin'],
            'email_verified': True,
        }

        users_data = [
            {
                'email': 'amal.benali@example.com',
                'first_name': 'Amal',
                'last_name': 'Ben Ali',
                'phone_number': '+21622111222',
                'roles': ['user'],
                'email_verified': True,
            },
            {
                'email': 'youssef.chaari@example.com',
                'first_name': 'Youssef',
                'last_name': 'Chaari',
                'phone_number': '+21623111333',
                'roles': ['user'],
                'email_verified': True,
            },
            {
                'email': 'salma.trabelsi@example.com',
                'first_name': 'Salma',
                'last_name': 'Trabelsi',
                'phone_number': '+21624111444',
                'roles': ['user'],
                'email_verified': True,
            },
        ]

        User.objects.create_superuser(password=default_password, **admin_data)

        for user_data in users_data:
            User.objects.create_user(password=default_password, **user_data)

        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded 4 users'))
