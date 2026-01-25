from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from webhooks.models import WebhookEvent, StripeEvent
import random


class Command(BaseCommand):
    help = 'Seeds the webhooks table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les webhooks existants
        WebhookEvent.objects.all().delete()
        StripeEvent.objects.all().delete()
        self.stdout.write('Webhooks tables cleared')
        
        # Créer des événements webhook
        self.stdout.write('\nCreating webhook events...')
        webhook_events_created = 0
        
        event_types = [
            'payment.succeeded',
            'payment.failed',
            'subscription.created',
            'subscription.updated',
            'subscription.deleted',
            'invoice.paid',
            'invoice.payment_failed',
            'customer.created',
            'customer.updated',
        ]
        
        for i in range(30):  # Créer 30 événements
            event_type = random.choice(event_types)
            source = random.choice(['stripe', 'stripe', 'stripe', 'paypal'])  # Majorité stripe
            
            # Créer un payload fictif
            payload = {
                'id': f'evt_{random.randint(100000, 999999)}',
                'type': event_type,
                'data': {
                    'object': {
                        'id': f'obj_{random.randint(100000, 999999)}',
                        'amount': random.randint(1000, 50000),
                        'currency': 'eur',
                        'status': random.choice(['succeeded', 'pending', 'failed']),
                    }
                },
                'created': int(timezone.now().timestamp()),
            }
            
            # Déterminer si l'événement a été traité
            processed = random.random() > 0.2  # 80% traités
            created_at = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23)
            )
            
            event = WebhookEvent.objects.create(
                event_type=event_type,
                payload=payload,
                source=source,
                processed=processed,
                processed_at=created_at + timedelta(seconds=random.randint(1, 60)) if processed else None,
                error_message='Processing error: Invalid customer ID' if not processed and random.random() > 0.7 else None,
                created_at=created_at,
            )
            webhook_events_created += 1
        
        self.stdout.write(f'  ✓ Created {webhook_events_created} webhook events')
        
        # Créer des événements Stripe (legacy)
        self.stdout.write('\nCreating Stripe events (legacy)...')
        stripe_events_created = 0
        
        stripe_event_types = [
            'charge.succeeded',
            'charge.failed',
            'customer.subscription.created',
            'customer.subscription.updated',
            'customer.subscription.deleted',
            'invoice.payment_succeeded',
            'invoice.payment_failed',
        ]
        
        statuses = ['processed', 'processed', 'processed', 'pending', 'failed']  # Majorité processed
        
        for i in range(20):  # Créer 20 événements Stripe
            event_type = random.choice(stripe_event_types)
            status = random.choice(statuses)
            
            data = {
                'id': f'ch_{random.randint(100000, 999999)}',
                'object': 'charge' if 'charge' in event_type else 'subscription' if 'subscription' in event_type else 'invoice',
                'amount': random.randint(1000, 50000),
                'currency': 'eur',
                'customer': f'cus_{random.randint(100000, 999999)}',
                'status': 'succeeded' if status == 'processed' else 'pending',
            }
            
            StripeEvent.objects.create(
                stripe_event_id=f'evt_{random.randint(100000000, 999999999)}',
                event_type=event_type,
                data=data,
                status=status,
                error_message='Invalid payment method' if status == 'failed' else None,
            )
            stripe_events_created += 1
        
        self.stdout.write(f'  ✓ Created {stripe_events_created} Stripe events (legacy)')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created webhooks:'))
        self.stdout.write(f'   • {webhook_events_created} webhook events')
        self.stdout.write(f'   • {stripe_events_created} Stripe events (legacy)')
