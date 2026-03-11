from django.core.management.base import BaseCommand
from vehicles.models import Vehicle, CarBrand, CarModel
from users.models import User


BRANDS_MODELS = {
    'Renault': ['Clio', 'Mégane', 'Captur', 'Kadjar', 'Scenic', 'Talisman', 'Twingo', 'Zoe', 'Arkana', 'Austral', 'Koleos', 'Laguna', 'Espace', 'Kangoo', 'Master', 'Trafic'],
    'Peugeot': ['108', '208', '308', '408', '508', '2008', '3008', '5008', 'Partner', 'Expert', 'Boxer', 'Rifter'],
    'Citroën': ['C1', 'C2', 'C3', 'C4', 'C5', 'C5 Aircross', 'C3 Aircross', 'Berlingo', 'Jumpy', 'Jumper', 'SpaceTourer'],
    'Volkswagen': ['Golf', 'Polo', 'Passat', 'Tiguan', 'T-Roc', 'T-Cross', 'Touareg', 'Sharan', 'Touran', 'Arteon', 'ID.3', 'ID.4', 'Caddy', 'Transporter'],
    'Toyota': ['Yaris', 'Corolla', 'Camry', 'RAV4', 'C-HR', 'Prius', 'Land Cruiser', 'Hilux', 'Auris', 'Aygo', 'Verso', 'Proace', 'GR86'],
    'BMW': ['118i', '120d', '316d', '320i', '330i', '520d', '530i', '730d', 'X1', 'X3', 'X5', 'X7', 'Z4', 'M3', 'M5', 'i3', 'i4', 'iX'],
    'Mercedes-Benz': ['A180', 'A200', 'C180', 'C200', 'C220d', 'E200', 'E220d', 'S400', 'GLA', 'GLB', 'GLC', 'GLE', 'GLS', 'CLA', 'CLS', 'EQC', 'EQA', 'Sprinter', 'Vito'],
    'Audi': ['A1', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'TT', 'R8', 'e-tron', 'e-tron GT', 'S3', 'S5', 'RS3'],
    'Ford': ['Fiesta', 'Focus', 'Mondeo', 'Kuga', 'Puma', 'Explorer', 'Mustang', 'Mustang Mach-E', 'Ranger', 'Transit', 'Transit Custom', 'Tourneo', 'EcoSport'],
    'Hyundai': ['i10', 'i20', 'i30', 'IONIQ', 'IONIQ 5', 'IONIQ 6', 'Tucson', 'Santa Fe', 'Kona', 'ix35', 'ix20', 'Nexo'],
    'Kia': ['Picanto', 'Rio', 'Ceed', 'ProCeed', 'Sportage', 'Stonic', 'Niro', 'EV6', 'Sorento', 'Telluride', 'Carnival', 'Soul'],
    'Fiat': ['500', '500X', '500L', 'Panda', 'Tipo', 'Egea', 'Punto', 'Bravo', 'Doblo', 'Ducato', 'Scudo', 'Fiorino'],
    'Dacia': ['Sandero', 'Logan', 'Duster', 'Lodgy', 'Dokker', 'Spring', 'Jogger', 'Bigster'],
    'Tesla': ['Model 3', 'Model S', 'Model X', 'Model Y', 'Cybertruck', 'Roadster'],
    'Nissan': ['Micra', 'Juke', 'Qashqai', 'X-Trail', 'Leaf', 'Ariya', 'Note', 'Navara', 'NV200', 'Townstar'],
    'Seat': ['Ibiza', 'Leon', 'Arona', 'Ateca', 'Tarraco', 'Mii', 'Toledo', 'Alhambra'],
    'Skoda': ['Fabia', 'Scala', 'Octavia', 'Superb', 'Kamiq', 'Karoq', 'Kodiaq', 'Enyaq'],
    'Opel': ['Corsa', 'Astra', 'Mokka', 'Crossland', 'Grandland', 'Insignia', 'Zafira', 'Vivaro', 'Movano', 'Combo'],
    'Mazda': ['Mazda2', 'Mazda3', 'Mazda6', 'CX-3', 'CX-30', 'CX-5', 'CX-60', 'MX-5', 'MX-30'],
    'Honda': ['Jazz', 'Civic', 'HR-V', 'CR-V', 'ZR-V', 'e', 'e:Ny1', 'Accord', 'Legend'],
    'Volvo': ['V40', 'V60', 'V90', 'S60', 'S90', 'XC40', 'XC60', 'XC90', 'C40', 'EX30', 'EX90'],
    'Land Rover': ['Defender', 'Discovery', 'Discovery Sport', 'Range Rover', 'Range Rover Sport', 'Range Rover Velar', 'Range Rover Evoque', 'Freelander'],
    'Jeep': ['Renegade', 'Compass', 'Cherokee', 'Grand Cherokee', 'Wrangler', 'Gladiator', 'Avenger'],
    'Alfa Romeo': ['MiTo', 'Giulietta', 'Giulia', 'Stelvio', 'Tonale', '4C', 'GTV'],
    'Porsche': ['911', 'Cayenne', 'Macan', 'Panamera', 'Taycan', 'Boxster', 'Cayman'],
    'Subaru': ['Impreza', 'Legacy', 'Outback', 'Forester', 'XV', 'Crosstrek', 'BRZ', 'WRX'],
    'Mitsubishi': ['Colt', 'Lancer', 'Eclipse Cross', 'ASX', 'Outlander', 'L200', 'Pajero', 'Space Star'],
    'Suzuki': ['Swift', 'Baleno', 'Vitara', 'S-Cross', 'Jimny', 'Ignis', 'Across', 'Swace'],
    'MINI': ['One', 'Cooper', 'Cooper S', 'Clubman', 'Countryman', 'Paceman', 'Cabrio', 'Electric'],
    'Lexus': ['CT', 'IS', 'ES', 'GS', 'LS', 'NX', 'RX', 'UX', 'LC', 'LX', 'RZ'],
    'Infiniti': ['Q30', 'Q50', 'Q60', 'Q70', 'QX30', 'QX50', 'QX70', 'QX80'],
    'Jaguar': ['E-Pace', 'F-Pace', 'I-Pace', 'XE', 'XF', 'XJ', 'F-Type'],
    'Chevrolet': ['Spark', 'Aveo', 'Cruze', 'Malibu', 'Camaro', 'Corvette', 'Blazer', 'Equinox', 'Trailblazer'],
    'Chrysler': ['300', 'Pacifica', 'Voyager'],
    'Dodge': ['Charger', 'Challenger', 'Durango', 'Journey', 'Viper'],
    'Ram': ['1500', '2500', '3500', 'ProMaster'],
    'GMC': ['Sierra', 'Canyon', 'Terrain', 'Acadia', 'Yukon', 'Envoy'],
    'Cadillac': ['CT4', 'CT5', 'XT4', 'XT5', 'XT6', 'Escalade', 'Lyriq'],
    'Lincoln': ['Corsair', 'Nautilus', 'Aviator', 'Navigator', 'Continental'],
    'Buick': ['Encore', 'Envision', 'Enclave', 'LaCrosse'],
    'Acura': ['ILX', 'TLX', 'RDX', 'MDX', 'NSX', 'Integra'],
    'Genesis': ['G70', 'G80', 'G90', 'GV70', 'GV80', 'GV60'],
    'Maserati': ['Ghibli', 'Quattroporte', 'Levante', 'GranTurismo', 'GranCabrio', 'MC20', 'Grecale'],
    'Ferrari': ['Roma', '296 GTB', 'SF90 Stradale', 'F8 Tributo', '812 Superfast', 'Purosangue', 'Portofino'],
    'Lamborghini': ['Huracán', 'Urus', 'Revuelto', 'Sian'],
    'Bentley': ['Continental GT', 'Flying Spur', 'Bentayga', 'Mulsanne'],
    'Rolls-Royce': ['Ghost', 'Phantom', 'Wraith', 'Dawn', 'Cullinan', 'Spectre'],
    'Aston Martin': ['Vantage', 'DB11', 'DBS', 'DBX', 'Valkyrie'],
    'McLaren': ['Artura', '720S', '765LT', 'GT', 'Elva'],
    'Bugatti': ['Chiron', 'Veyron', 'Divo', 'Centodieci'],
    'Polestar': ['2', '3', '4', '6'],
    'Rivian': ['R1T', 'R1S'],
    'Lucid': ['Air', 'Gravity'],
    'BYD': ['Atto 3', 'Han', 'Tang', 'Dolphin', 'Seal', 'Song', 'Yuan'],
    'MG': ['ZS', 'MG5', 'MG4', 'HS', 'Marvel R', 'Cyberster'],
    'Cupra': ['Formentor', 'Ateca', 'Born', 'Leon', 'Terramar'],
    'DS': ['DS 3', 'DS 4', 'DS 7', 'DS 9', 'DS 3 Crossback', 'DS 7 Crossback'],
    'Lancia': ['Ypsilon', 'Delta'],
}


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
            # Utilisateur : Amal Benali
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
            # Utilisateur : Youssef Chaari
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
            # Utilisateur : Salma Trabelsi
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

        # Seed all brands and models from BRANDS_MODELS dict
        brands_to_create = [CarBrand(name=name) for name in BRANDS_MODELS]
        CarBrand.objects.bulk_create(brands_to_create, ignore_conflicts=True)
        brands = {b.name: b for b in CarBrand.objects.all()}

        models_to_create = []
        for brand_name, model_names in BRANDS_MODELS.items():
            brand = brands.get(brand_name)
            if not brand:
                continue
            for model_name in model_names:
                models_to_create.append(CarModel(name=model_name, brand=brand))
        CarModel.objects.bulk_create(models_to_create, ignore_conflicts=True)
        created_models = CarModel.objects.count()

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(created_vehicles)} vehicles'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {len(brands)} car brands'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {created_models} car models'))
