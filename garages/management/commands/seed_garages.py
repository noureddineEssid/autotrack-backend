from django.core.management.base import BaseCommand
from garages.models import Garage, GarageReview


class Command(BaseCommand):
    help = 'Seeds the garages table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les garages existants
        Garage.objects.all().delete()
        self.stdout.write('Garages table cleared')
        
        # Créer les garages de test
        garages_data = [
            {
                'name': 'Garage Moderne Paris',
                'email': 'contact@garage-moderne-paris.fr',
                'phone': '+33142857890',
                'address': '123 Avenue des Champs-Élysées',
                'city': 'Paris',
                'postal_code': '75008',
                'country': 'France',
                'location': {
                    'type': 'Point',
                    'coordinates': [2.3070, 48.8716]  # [longitude, latitude]
                },
                'description': 'Garage spécialisé dans l\'entretien et la réparation de véhicules toutes marques.',
                'specialties': ['Vidange', 'Révision', 'Freinage', 'Climatisation'],
                'certifications': ['ISO 9001', 'Qualité Renault'],
                'average_rating': 4.5,
                'total_reviews': 127,
            },
            {
                'name': 'Auto Service Lyon',
                'email': 'info@autoservice-lyon.fr',
                'phone': '+33478965412',
                'address': '45 Rue de la République',
                'city': 'Lyon',
                'postal_code': '69002',
                'country': 'France',
                'location': {
                    'type': 'Point',
                    'coordinates': [4.8357, 45.7640]
                },
                'description': 'Expert en diagnostic et réparation électronique automobile.',
                'specialties': ['Diagnostic', 'Électronique', 'Pneumatiques', 'Carrosserie'],
                'certifications': ['ISO 14001', 'PSA Expert'],
                'average_rating': 4.8,
                'total_reviews': 243,
            },
            {
                'name': 'Garage Express Marseille',
                'email': 'contact@garage-express-marseille.fr',
                'phone': '+33491225588',
                'address': '78 Boulevard Michelet',
                'city': 'Marseille',
                'postal_code': '13008',
                'country': 'France',
                'location': {
                    'type': 'Point',
                    'coordinates': [5.3698, 43.2965]
                },
                'description': 'Intervention rapide et service de qualité pour tous types de véhicules.',
                'specialties': ['Entretien Rapide', 'Vidange', 'Pneus', 'Contrôle Technique'],
                'certifications': ['Qualité Peugeot'],
                'average_rating': 4.2,
                'total_reviews': 89,
            },
            {
                'name': 'Mécanique Pro Toulouse',
                'email': 'contact@mecanique-pro-toulouse.fr',
                'phone': '+33561347890',
                'address': '12 Allée Jean Jaurès',
                'city': 'Toulouse',
                'postal_code': '31000',
                'country': 'France',
                'location': {
                    'type': 'Point',
                    'coordinates': [1.4442, 43.6047]
                },
                'description': 'Garage familial avec plus de 30 ans d\'expérience.',
                'specialties': ['Mécanique Générale', 'Boîte de Vitesse', 'Embrayage', 'Distribution'],
                'certifications': ['ISO 9001', 'Citroën Service'],
                'average_rating': 4.7,
                'total_reviews': 156,
            },
            {
                'name': 'Centre Auto Bordeaux',
                'email': 'info@centreauto-bordeaux.fr',
                'phone': '+33556788899',
                'address': '56 Cours de l\'Intendance',
                'city': 'Bordeaux',
                'postal_code': '33000',
                'country': 'France',
                'location': {
                    'type': 'Point',
                    'coordinates': [-0.5792, 44.8378]
                },
                'description': 'Centre automobile complet avec équipements dernière génération.',
                'specialties': ['Toutes Réparations', 'Géométrie', 'Parallélisme', 'Amortisseurs'],
                'certifications': ['ISO 9001', 'ISO 14001', 'Qualité BMW'],
                'average_rating': 4.6,
                'total_reviews': 198,
            },
        ]
        
        created_garages = []
        for garage_data in garages_data:
            garage = Garage.objects.create(**garage_data)
            created_garages.append(garage)
            self.stdout.write(f'  ✓ Created garage: {garage.name}')
        
        # Créer quelques avis pour les garages
        self.stdout.write('\nCreating reviews...')
        from users.models import User
        
        users = list(User.objects.all()[:5])
        reviews_created = 0
        if users:
            reviews_data = [
                {'garage': created_garages[0], 'reviewer_name': f'{users[0].first_name} {users[0].last_name}', 'reviewer_email': users[0].email, 'rating': 5, 'comment': 'Service impeccable, très professionnel !'},
                {'garage': created_garages[0], 'reviewer_name': f'{users[1].first_name} {users[1].last_name}', 'reviewer_email': users[1].email, 'rating': 4, 'comment': 'Bon rapport qualité-prix'},
                {'garage': created_garages[1], 'reviewer_name': f'{users[2].first_name} {users[2].last_name}', 'reviewer_email': users[2].email, 'rating': 5, 'comment': 'Excellent diagnostic et réparation rapide'},
                {'garage': created_garages[1], 'reviewer_name': f'{users[3].first_name} {users[3].last_name}', 'reviewer_email': users[3].email, 'rating': 5, 'comment': 'Je recommande vivement ce garage'},
                {'garage': created_garages[2], 'reviewer_name': f'{users[0].first_name} {users[0].last_name}', 'reviewer_email': users[0].email, 'rating': 4, 'comment': 'Service rapide comme promis'},
                {'garage': created_garages[3], 'reviewer_name': f'{users[1].first_name} {users[1].last_name}', 'reviewer_email': users[1].email, 'rating': 5, 'comment': 'Équipe sympathique et compétente'},
                {'garage': created_garages[4], 'reviewer_name': f'{users[2].first_name} {users[2].last_name}', 'reviewer_email': users[2].email, 'rating': 5, 'comment': 'Matériel de pointe, travail soigné'},
            ]
            
            for review_data in reviews_data:
                GarageReview.objects.create(**review_data)
                reviews_created += 1
            
            self.stdout.write(f'  ✓ Created {reviews_created} reviews')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {len(created_garages)} garages with reviews'))
