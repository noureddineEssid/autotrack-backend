from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from webhooks.models import WebhookEvent, StripeEvent
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = 'Seeds the webhooks table with realistic data'

    def handle(self, *args, **kwargs):
        WebhookEvent.objects.all().delete()
        StripeEvent.objects.all().delete()
        self.stdout.write('Webhooks tables cleared')

        subscriptions = list(Subscription.objects.select_related('user'))

        self.stdout.write('\nCreating webhook events...')
        webhook_events_created = 0

        for subscription in subscriptions:
            payload = {
                'id': f'evt_{subscription.id}',
                'type': 'subscription.created',
                'data': {
                    'object': {
                        'id': subscription.stripe_subscription_id or f'sub_{subscription.id}',
                        'customer': subscription.stripe_customer_id or f'cus_{subscription.user.id}',
                        'status': subscription.status,
                        'plan_code': subscription.plan_code,
                        'amount': 0,
                        'currency': 'eur',
                    }
                },
                'created': int(timezone.now().timestamp()),
            }

            WebhookEvent.objects.create(
                event_type='subscription.created',
                payload=payload,
                source='stripe',
                processed=True,
                processed_at=timezone.now() - timedelta(minutes=2),
                created_at=timezone.now() - timedelta(minutes=5),
            )
            webhook_events_created += 1

        self.stdout.write(f'  ✓ Created {webhook_events_created} webhook events')

        self.stdout.write('\nCreating Stripe events (legacy)...')
        stripe_events_created = 0

        for subscription in subscriptions:
            data = {
                'id': subscription.stripe_subscription_id or f'sub_{subscription.id}',
                'object': 'subscription',
                'amount': 0,
                'currency': 'eur',
                'customer': subscription.stripe_customer_id or f'cus_{subscription.user.id}',
                'status': 'active',
            }

            StripeEvent.objects.create(
                stripe_event_id=f'evt_{subscription.id}',
                event_type='customer.subscription.created',
                data=data,
                status='processed',
            )
            stripe_events_created += 1

        self.stdout.write(f'  ✓ Created {stripe_events_created} Stripe events (legacy)')

        self.stdout.write(self.style.SUCCESS('\n✅ Successfully created webhooks:'))
        self.stdout.write(f'   • {webhook_events_created} webhook events')
        self.stdout.write(f'   • {stripe_events_created} Stripe events (legacy)')
