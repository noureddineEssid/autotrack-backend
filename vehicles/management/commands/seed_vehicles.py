from django.core.management.base import BaseCommand
from vehicles.models import Vehicle, CarBrand, CarModel
from users.models import User
import requests
from datetime import datetime


class Command(BaseCommand):
    help = 'Seeds the vehicles, car brands, and car models tables with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les tables
        Vehicle.objects.all().delete()
        CarBrand.objects.all().delete()
        CarModel.objects.all().delete()
        self.stdout.write('Tables cleared')
        
        # Récupérer les utilisateurs
        users = list(User.objects.all()[:4])
        if len(users) < 2:
            self.stdout.write(self.style.ERROR('Pas assez d\'utilisateurs. Exécutez seed_users d\'abord.'))
            return
        
        # Créer des véhicules de test
        vehicles_data = [
            {
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2018,
                'license_plate': 'AA-123-BB',
                'vin': 'JT2BF22K1W0123456',
                'owner': users[0],
                'fuel_type': 'gasoline',
                'transmission': 'automatic'
            },
            {
                'make': 'Renault',
                'model': 'Clio',
                'year': 2020,
                'license_plate': 'CC-456-DD',
                'vin': 'VF1RFA00912345678',
                'owner': users[1] if len(users) > 1 else users[0],
                'fuel_type': 'diesel',
                'transmission': 'manual'
            },
            {
                'make': 'Peugeot',
                'model': '308',
                'year': 2019,
                'license_plate': 'EE-789-FF',
                'vin': 'VF34C5FSC12345678',
                'owner': users[0],
                'fuel_type': 'hybrid',
                'transmission': 'automatic'
            }
        ]
        
        created_vehicles = []
        for vehicle_data in vehicles_data:
            vehicle = Vehicle.objects.create(**vehicle_data)
            created_vehicles.append(vehicle)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(created_vehicles)} vehicles'))
        
        # Récupérer les marques depuis l'API NHTSA
        brands = []
        try:
            response = requests.get(
                'https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'Results' in data:
                    brands = data['Results']
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Could not fetch brands from API: {str(e)}'))
        
        # Liste des marques populaires
        popular_brands = [
            'Toyota', 'Volkswagen', 'Ford', 'Honda', 'Chevrolet', 'Nissan', 'Hyundai', 'Kia', 'Renault', 'Peugeot',
            'Mercedes-Benz', 'BMW', 'Fiat', 'Audi', 'Skoda', 'Opel', 'Mazda', 'Citroën', 'Jeep', 'Dacia',
            'Seat', 'Subaru', 'Volvo', 'Mini', 'Land Rover', 'Suzuki', 'Mitsubishi', 'Lexus', 'Porsche', 'Jaguar',
            'Alfa Romeo', 'Tesla', 'Chrysler', 'Dodge', 'Ram', 'Buick', 'Cadillac', 'GMC', 'Lincoln', 'Infiniti',
            'Acura', 'Genesis', 'Saab', 'Smart', 'Isuzu', 'SsangYong', 'Great Wall', 'Geely', 'BYD', 'Haval',
            'Pontiac', 'Saturn', 'Scion', 'Oldsmobile', 'Hummer', 'Daewoo', 'Rover', 'Lancia', 'Proton', 'Perodua',
            'Tata', 'Mahindra', 'Chery', 'FAW', 'Dongfeng', 'Zotye', 'BAIC', 'JAC', 'Foton', 'Lifan',
            'Maruti', 'Holden', 'HSV', 'Vauxhall', 'Morgan', 'Pagani', 'Bugatti', 'Bentley', 'Rolls-Royce', 'Aston Martin',
            'McLaren', 'Lotus', 'Caterham', 'Daihatsu', 'Luxgen', 'Wuling', 'Baojun', 'Polestar', 'Cupra', 'Abarth',
            'DS', 'Datsun', 'Eagle', 'Fisker', 'GAC', 'Hino', 'MAN', 'Peterbilt', 'Kenworth', 'Western Star',
            'Freightliner', 'Navistar', 'International', 'Mack', 'Sterling', 'Yutong', 'King Long', 'Setra', 'Neoplan', 'Iveco'
        ]
        
        # Fonction de normalisation
        def normalize(text):
            if not text:
                return ''
            import unicodedata
            text = text.upper().replace('-', '').replace(' ', '')
            return ''.join(c for c in unicodedata.normalize('NFD', text) 
                         if unicodedata.category(c) != 'Mn')
        
        normalized_popular = [normalize(b) for b in popular_brands]
        
        # Filtrer les marques populaires
        filtered_brands = [
            b for b in brands 
            if normalize(b.get('Make_Name', b.get('name', ''))) in normalized_popular
        ]
        
        created_brands = []
        for brand in filtered_brands[:100]:  # Limiter à 100 marques
            try:
                car_brand = CarBrand.objects.create(
                    name=brand.get('Make_Name', brand.get('name', 'Unknown'))
                )
                created_brands.append(car_brand)
            except Exception:
                pass
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(created_brands)} car brands'))
        
        # Créer les modèles pour chaque marque
        total_models = 0
        for brand in created_brands[:20]:  # Limiter aux 20 premières marques pour ne pas surcharger
            models = []
            try:
                response = requests.get(
                    f'https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{brand.name}?format=json',
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'Results' in data:
                        models = data['Results']
            except Exception:
                continue
            
            for model in models[:50]:  # Limiter à 50 modèles par marque
                try:
                    CarModel.objects.create(
                        name=model.get('Model_Name', model.get('name', 'Unknown')),
                        brand=brand
                    )
                    total_models += 1
                except Exception:
                    pass
        
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {total_models} car models'))
