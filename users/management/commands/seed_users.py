from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the users table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les utilisateurs existants
        User.objects.all().delete()
        self.stdout.write('Users table cleared')
        
        # Créer les utilisateurs de test
        users_data = [
            {
                'email': 'john.smith@example.com',
                'username': 'john.smith@example.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'phone_number': '+1234567890',
            },
            {
                'email': 'sarah.johnson@example.com',
                'username': 'sarah.johnson@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'phone_number': '+1234567891',
            },
            {
                'email': 'michael.chen@example.com',
                'username': 'michael.chen@example.com',
                'first_name': 'Michael',
                'last_name': 'Chen',
                'phone_number': '+1234567892',
            },
            {
                'email': 'emily.rodriguez@example.com',
                'username': 'emily.rodriguez@example.com',
                'first_name': 'Emily',
                'last_name': 'Rodriguez',
                'phone_number': '+1234567893',
            },
            {
                'email': 'david.kim@example.com',
                'username': 'david.kim@example.com',
                'first_name': 'David',
                'last_name': 'Kim',
                'phone_number': '+1234567894',
            },
        ]
        
        created_count = 0
        for user_data in users_data:
            user = User.objects.create_user(
                password='123456789@@',
                **user_data
            )
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {created_count} users'))
