from django.core.management.base import BaseCommand
from documents.models import Document
from vehicles.models import Vehicle
from users.models import User
from django.core.files.base import ContentFile
import random


class Command(BaseCommand):
    help = 'Seeds the documents table'

    def handle(self, *args, **kwargs):
        # Nettoyer
        Document.objects.all().delete()
        self.stdout.write('Table cleared')
        
        # Récupérer véhicules et utilisateurs
        vehicles = list(Vehicle.objects.all()[:3])
        users = list(User.objects.all()[:3])
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Run seed_vehicles first.'))
            return
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Run seed_users first.'))
            return
        
        doc_types = ['invoice', 'insurance', 'registration', 'inspection', 'maintenance', 'other']
        doc_titles = [
            'Facture révision annuelle',
            'Contrat assurance',
            'Carte grise',
            'Contrôle technique',
            'Carnet d\'entretien',
            'Facture pneumatiques',
        ]
        
        documents_created = []
        
        for i in range(min(len(vehicles), len(users))):
            vehicle = vehicles[i]
            user = users[i]
            num_docs = random.randint(2, 4)
            
            for j in range(num_docs):
                doc_type = random.choice(doc_types)
                title = random.choice(doc_titles)
                
                # Créer un fichier factice
                file_content = ContentFile(f'Mock document content for {title}'.encode('utf-8'))
                file_content.name = f'document_{i}_{j}.pdf'
                
                document = Document.objects.create(
                    user=user,
                    vehicle=vehicle,
                    title=f'{title} - {vehicle.make} {vehicle.model}',
                    description=f'Document de type {doc_type}',
                    document_type=doc_type,
                    file=file_content,
                    file_size=random.randint(1024, 1024000),
                    mime_type='application/pdf',
                    is_analyzed=random.choice([True, False]),
                )
                documents_created.append(document)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(documents_created)} documents'))
        
        stats = {}
        for doc_type, _ in Document.DOCUMENT_TYPE_CHOICES:
            count = Document.objects.filter(document_type=doc_type).count()
            if count > 0:
                stats[doc_type] = count
        
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'  - {len(documents_created)} total documents')
        for doc_type, count in stats.items():
            self.stdout.write(f'  - {count} {doc_type}')
