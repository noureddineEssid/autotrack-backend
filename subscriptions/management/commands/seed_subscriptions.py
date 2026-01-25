from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import Subscription
from users.models import User
from plans.models import Plan
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seeds the subscriptions table'

    def handle(self, *args, **kwargs):
        # Nettoyer
        Subscription.objects.all().delete()
        self.stdout.write('Table cleared')
        
        now = timezone.now()
        
        # Récupérer les utilisateurs et plans
        users = list(User.objects.all()[:3])
        try:
            free_plan = Plan.objects.get(name='Free')
            standard_plan = Plan.objects.get(name='Standard')
            premium_plan = Plan.objects.get(name='Premium')
        except Plan.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️  Plans not found. Run seed_plans first.'))
            return
        
        if len(users) < 3:
            self.stdout.write(self.style.WARNING('⚠️  Not enough users. Run seed_users first.'))
            return
        
        # Créer les abonnements
        subscriptions = [
            Subscription.objects.create(
                user=users[0],
                plan=free_plan,
                status='active',
                current_period_start=now - timedelta(days=30),
                current_period_end=now + timedelta(days=335),
                cancel_at_period_end=False,
            ),
            Subscription.objects.create(
                user=users[1],
                plan=standard_plan,
                status='active',
                current_period_start=now - timedelta(days=15),
                current_period_end=now + timedelta(days=15),
                cancel_at_period_end=False,
                stripe_subscription_id='sub_mock_standard_12345',
                stripe_customer_id='cus_mock_67890',
            ),
            Subscription.objects.create(
                user=users[2],
                plan=premium_plan,
                status='active',
                current_period_start=now - timedelta(days=60),
                current_period_end=now - timedelta(days=30),
                cancel_at_period_end=False,
                stripe_subscription_id='sub_mock_premium_54321',
                stripe_customer_id='cus_mock_09876',
            ),
        ]
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(subscriptions)} subscriptions'))
        self.stdout.write(f'  - 1 free subscription')
        self.stdout.write(f'  - 1 standard subscription')
        self.stdout.write(f'  - 1 premium subscription')
