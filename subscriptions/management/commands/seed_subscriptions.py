from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import Subscription, SubscriptionHistory
from subscriptions.plan_catalog import get_plan
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the subscriptions table'

    def handle(self, *args, **kwargs):
        Subscription.objects.all().delete()
        SubscriptionHistory.objects.all().delete()
        self.stdout.write('Table cleared')

        now = timezone.now()

        users_by_email = {
            user.email: user
            for user in User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        }

        if len(users_by_email) < 3:
            self.stdout.write(self.style.WARNING('⚠️  Not enough users. Run seed_users first.'))
            return

        plan_free = get_plan('free')
        plan_standard = get_plan('standard')
        plan_premium = get_plan('premium')

        subscriptions = []
        subscriptions.append(
            Subscription.objects.create(
                user=users_by_email['amal.benali@example.com'],
                plan_code='free',
                plan_name=plan_free['name'],
                status='active',
                current_period_start=now - timedelta(days=5),
                current_period_end=now + timedelta(days=25),
                cancel_at_period_end=False,
            )
        )
        subscriptions.append(
            Subscription.objects.create(
                user=users_by_email['youssef.chaari@example.com'],
                plan_code='standard',
                plan_name=plan_standard['name'],
                status='active',
                current_period_start=now - timedelta(days=12),
                current_period_end=now + timedelta(days=18),
                cancel_at_period_end=False,
                stripe_subscription_id='sub_mock_standard_2025',
                stripe_customer_id='cus_mock_youssef_01',
            )
        )
        subscriptions.append(
            Subscription.objects.create(
                user=users_by_email['salma.trabelsi@example.com'],
                plan_code='premium',
                plan_name=plan_premium['name'],
                status='active',
                current_period_start=now - timedelta(days=20),
                current_period_end=now + timedelta(days=10),
                cancel_at_period_end=False,
                stripe_subscription_id='sub_mock_premium_2025',
                stripe_customer_id='cus_mock_salma_01',
            )
        )

        for subscription in subscriptions:
            SubscriptionHistory.objects.create(
                subscription=subscription,
                event_type='created',
                new_status=subscription.status,
                metadata={'plan_code': subscription.plan_code},
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(subscriptions)} subscriptions'))
        self.stdout.write('  - 1 free subscription')
        self.stdout.write('  - 1 standard subscription')
        self.stdout.write('  - 1 premium subscription')
