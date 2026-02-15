from django.core.management.base import BaseCommand
from vehicles.models import Vehicle, CarBrand, CarModel
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the vehicles, car brands, and car models tables with realistic data'

    def handle(self, *args, **kwargs):
        Vehicle.objects.all().delete()
        CarBrand.objects.all().delete()
        CarModel.objects.all().delete()
        self.stdout.write('Tables cleared')

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

        if len(users) < 3:
            self.stdout.write(self.style.ERROR('Pas assez d\'utilisateurs. Exécutez seed_users d\'abord.'))
            return

        vehicles_data = [
            # Free plan user (<= 3 vehicles)
            {
                'owner': users['amal.benali@example.com'],
                'make': 'Renault',
                'model': 'Clio',
                'year': 2019,
                'license_plate': 'TU-214-AB',
                'vin': 'VF1RFA009KJ123456',
                'color': 'Blanc',
                'fuel_type': 'diesel',
                'transmission': 'manual',
            },
            {
                'owner': users['amal.benali@example.com'],
                'make': 'Toyota',
                'model': 'Yaris',
                'year': 2017,
                'license_plate': 'TU-987-CD',
                'vin': 'JTDBR32E201234567',
                'color': 'Gris',
                'fuel_type': 'gasoline',
                'transmission': 'automatic',
            },
            # Standard plan user (<= 10 vehicles)
            {
                'owner': users['youssef.chaari@example.com'],
                'make': 'Peugeot',
                'model': '308',
                'year': 2020,
                'license_plate': 'TU-556-EF',
                'vin': 'VF34C5FSCM1234567',
                'color': 'Bleu',
                'fuel_type': 'diesel',
                'transmission': 'manual',
            },
            {
                'owner': users['youssef.chaari@example.com'],
                'make': 'Volkswagen',
                'model': 'Golf',
                'year': 2018,
                'license_plate': 'TU-612-GH',
                'vin': 'WVWZZZ1KZJW123456',
                'color': 'Noir',
                'fuel_type': 'gasoline',
                'transmission': 'manual',
            },
            {
                'owner': users['youssef.chaari@example.com'],
                'make': 'Hyundai',
                'model': 'Tucson',
                'year': 2021,
                'license_plate': 'TU-778-JK',
                'vin': 'KMHJT81B4MU123456',
                'color': 'Rouge',
                'fuel_type': 'hybrid',
                'transmission': 'automatic',
            },
            {
                'owner': users['youssef.chaari@example.com'],
                'make': 'Fiat',
                'model': '500',
                'year': 2016,
                'license_plate': 'TU-443-LM',
                'vin': 'ZFA3120000J123456',
                'color': 'Blanc',
                'fuel_type': 'gasoline',
                'transmission': 'manual',
            },
            {
                'owner': users['youssef.chaari@example.com'],
                'make': 'Kia',
                'model': 'Sportage',
                'year': 2019,
                'license_plate': 'TU-991-NP',
                'vin': 'KNAKU81B0K5123456',
                'color': 'Gris',
                'fuel_type': 'diesel',
                'transmission': 'automatic',
            },
            # Premium plan user (unlimited vehicles, seeded with 8)
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'BMW',
                'model': '320i',
                'year': 2021,
                'license_plate': 'TU-110-QR',
                'vin': 'WBA8E1C53MK123456',
                'color': 'Noir',
                'fuel_type': 'gasoline',
                'transmission': 'automatic',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Mercedes-Benz',
                'model': 'C200',
                'year': 2020,
                'license_plate': 'TU-223-ST',
                'vin': 'WDDWF8DB9LR123456',
                'color': 'Gris',
                'fuel_type': 'gasoline',
                'transmission': 'automatic',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Audi',
                'model': 'A3',
                'year': 2019,
                'license_plate': 'TU-334-UV',
                'vin': 'WAUZZZ8V0K1123456',
                'color': 'Bleu',
                'fuel_type': 'gasoline',
                'transmission': 'automatic',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Tesla',
                'model': 'Model 3',
                'year': 2022,
                'license_plate': 'TU-445-WX',
                'vin': '5YJ3E1EA0NF123456',
                'color': 'Blanc',
                'fuel_type': 'electric',
                'transmission': 'automatic',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Dacia',
                'model': 'Duster',
                'year': 2018,
                'license_plate': 'TU-556-YZ',
                'vin': 'UU1HSDAA6J1234567',
                'color': 'Orange',
                'fuel_type': 'diesel',
                'transmission': 'manual',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Peugeot',
                'model': '3008',
                'year': 2022,
                'license_plate': 'TU-667-AA',
                'vin': 'VF3MRHNS0NS123456',
                'color': 'Gris',
                'fuel_type': 'hybrid',
                'transmission': 'automatic',
            },
            {
                'owner': users['salma.trabelsi@example.com'],
                'make': 'Citroen',
                'model': 'C4',
                'year': 2021,
                'license_plate': 'TU-778-BB',
                'vin': 'VR7BBAHH0MG123456',
                'color': 'Blanc',
                'fuel_type': 'gasoline',
                'transmission': 'automatic',
            },
        ]

        created_vehicles = []
        for vehicle_data in vehicles_data:
            created_vehicles.append(Vehicle.objects.create(**vehicle_data))

        brand_names = sorted({vehicle['make'] for vehicle in vehicles_data})
        brands = {name: CarBrand.objects.create(name=name) for name in brand_names}

        created_models = 0
        unique_models = {(vehicle['make'], vehicle['model']) for vehicle in vehicles_data}
        for make, model in unique_models:
            brand = brands[make]
            CarModel.objects.get_or_create(name=model, brand=brand)
            created_models += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(created_vehicles)} vehicles'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(brands)} car brands'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {created_models} car models'))
