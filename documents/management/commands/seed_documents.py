from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from documents.models import Document
from vehicles.models import Vehicle
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the documents table'

    def handle(self, *args, **kwargs):
        Document.objects.all().delete()
        self.stdout.write('Table cleared')

        users = {
            user.email: user
            for user in User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        }

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Run seed_users first.'))
            return

        vehicles_by_user = {
            email: list(Vehicle.objects.filter(owner=user))
            for email, user in users.items()
        }

        if not any(vehicles_by_user.values()):
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Run seed_vehicles first.'))
            return

        plan_document_targets = {
            'amal.benali@example.com': 12,     # free (<= 50)
            'youssef.chaari@example.com': 40,  # standard (<= 200)
            'salma.trabelsi@example.com': 80,  # premium (<= 1000)
        }

        doc_templates = [
            ('insurance', 'Attestation assurance annuelle', 450_000),
            ('registration', 'Carte grise', 350_000),
            ('inspection', 'Controle technique', 600_000),
            ('maintenance', 'Carnet entretien', 700_000),
            ('invoice', 'Facture reparation', 520_000),
            ('invoice', 'Facture pneus', 420_000),
            ('other', 'Justificatif depenses', 280_000),
        ]

        documents_created = []

        for email, user in users.items():
            vehicles = vehicles_by_user.get(email, [])
            if not vehicles:
                continue

            target_count = plan_document_targets[email]
            for i in range(target_count):
                vehicle = vehicles[i % len(vehicles)]
                doc_type, base_title, size_bytes = doc_templates[i % len(doc_templates)]

                file_content = ContentFile(b'%PDF-1.4 Mock document')
                file_content.name = f'{user.id}_document_{i + 1}.pdf'

                document = Document.objects.create(
                    user=user,
                    vehicle=vehicle,
                    title=f'{base_title} - {vehicle.make} {vehicle.model}',
                    description=f'Document {doc_type} associe au vehicule {vehicle.license_plate}',
                    document_type=doc_type,
                    file=file_content,
                    file_size=size_bytes,
                    mime_type='application/pdf',
                    is_analyzed=True,
                )
                documents_created.append(document)

        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(documents_created)} documents'))

        stats = {}
        for doc_type, _ in Document.DOCUMENT_TYPE_CHOICES:
            count = Document.objects.filter(document_type=doc_type).count()
            if count > 0:
                stats[doc_type] = count

        self.stdout.write('\n📊 Summary:')
        self.stdout.write(f'  - {len(documents_created)} total documents')
        for doc_type, count in stats.items():
            self.stdout.write(f'  - {count} {doc_type}')
