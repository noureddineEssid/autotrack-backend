from django.core.management.base import BaseCommand
from webhooks.models import WebhookEvent


class Command(BaseCommand):
    help = 'Seeds the webhooks table with realistic data'

    def handle(self, *args, **kwargs):
        WebhookEvent.objects.all().delete()
        self.stdout.write('Webhooks tables cleared')
        self.stdout.write(self.style.SUCCESS('\n✅ Webhooks tables cleared (no seed data)'))
