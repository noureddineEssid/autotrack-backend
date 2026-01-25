from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
from bookings.models import GarageService, GarageAvailability, Booking, BookingReview
from garages.models import Garage
from users.models import User
from vehicles.models import Vehicle
import random


class Command(BaseCommand):
    help = 'Seeds the bookings table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les données existantes
        GarageService.objects.all().delete()
        GarageAvailability.objects.all().delete()
        Booking.objects.all().delete()
        self.stdout.write('Bookings tables cleared')
        
        garages = list(Garage.objects.all())
        users = list(User.objects.all())
        vehicles = list(Vehicle.objects.all())
        
        if not garages:
            self.stdout.write(self.style.WARNING('⚠️  No garages found. Please run seed_garages first.'))
            return
        
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return
        
        if not vehicles:
            self.stdout.write(self.style.WARNING('⚠️  No vehicles found. Please run seed_vehicles first.'))
            return
        
        # Créer les services pour chaque garage
        self.stdout.write('\nCreating garage services...')
        services_data = [
            {'name': 'Vidange Moteur', 'category': 'maintenance', 'duration_minutes': 45, 'price': 79.90, 'description': 'Vidange complète avec changement du filtre à huile'},
            {'name': 'Révision Complète', 'category': 'maintenance', 'duration_minutes': 120, 'price': 249.90, 'description': 'Révision selon les préconisations constructeur'},
            {'name': 'Changement Plaquettes de Frein', 'category': 'repair', 'duration_minutes': 90, 'price': 159.90, 'description': 'Changement des plaquettes avant ou arrière'},
            {'name': 'Diagnostic Électronique', 'category': 'diagnostic', 'duration_minutes': 60, 'price': 89.90, 'description': 'Diagnostic complet avec valise électronique'},
            {'name': 'Changement de Pneus', 'category': 'tire', 'duration_minutes': 60, 'price': 45.00, 'description': 'Montage et équilibrage (prix par pneu)'},
            {'name': 'Géométrie et Parallélisme', 'category': 'maintenance', 'duration_minutes': 45, 'price': 69.90, 'description': 'Réglage de la géométrie des trains roulants'},
            {'name': 'Contrôle Technique', 'category': 'diagnostic', 'duration_minutes': 30, 'price': 78.00, 'description': 'Contrôle technique réglementaire'},
            {'name': 'Climatisation', 'category': 'maintenance', 'duration_minutes': 90, 'price': 129.90, 'description': 'Recharge et désinfection de la climatisation'},
        ]
        
        created_services = []
        for garage in garages:
            for service_data in services_data:
                service = GarageService.objects.create(
                    garage=garage,
                    **service_data
                )
                created_services.append(service)
        
        self.stdout.write(f'  ✓ Created {len(created_services)} services')
        
        # Créer les disponibilités pour chaque garage
        self.stdout.write('\nCreating garage availabilities...')
        availabilities_created = 0
        
        # Créneaux horaires standards
        time_slots = [
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0)),
            (time(14, 0), time(16, 0)),
            (time(16, 0), time(18, 0)),
        ]
        
        for garage in garages:
            # Du lundi au vendredi
            for weekday in range(5):
                for start_time, end_time in time_slots:
                    GarageAvailability.objects.create(
                        garage=garage,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time,
                        max_bookings_per_slot=2
                    )
                    availabilities_created += 1
            
            # Samedi matin seulement
            for start_time, end_time in time_slots[:2]:
                GarageAvailability.objects.create(
                    garage=garage,
                    weekday=5,
                    start_time=start_time,
                    end_time=end_time,
                    max_bookings_per_slot=1
                )
                availabilities_created += 1
        
        self.stdout.write(f'  ✓ Created {availabilities_created} availability slots')
        
        # Créer des réservations
        self.stdout.write('\nCreating bookings...')
        booking_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        
        bookings_data = []
        today = timezone.now().date()
        
        for i in range(30):  # Créer 30 réservations
            user = random.choice(users)
            vehicle = random.choice([v for v in vehicles if v.owner == user] or vehicles)
            garage = random.choice(garages)
            service = random.choice([s for s in created_services if s.garage == garage])
            
            # Date entre -15 jours et +15 jours
            booking_date = today + timedelta(days=random.randint(-15, 15))
            booking_time = random.choice([time(8, 0), time(10, 0), time(14, 0), time(16, 0)])
            
            # Statut basé sur la date
            if booking_date < today:
                status = random.choice(['completed', 'cancelled', 'no_show'])
                payment_status = 'paid' if status == 'completed' else 'pending'
            elif booking_date == today:
                status = random.choice(['confirmed', 'in_progress'])
                payment_status = 'pending'
            else:
                status = random.choice(['pending', 'confirmed'])
                payment_status = 'pending'
            
            booking = Booking.objects.create(
                user=user,
                garage=garage,
                vehicle=vehicle,
                service=service,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_minutes=service.duration_minutes,
                status=status,
                customer_name=f"{user.first_name} {user.last_name}",
                customer_phone=user.phone_number or '+33612345678',
                customer_email=user.email,
                notes=random.choice(['', 'Véhicule qui fait un bruit anormal', 'Première visite', 'Client régulier']),
                estimated_price=service.price,
                final_price=service.price if status == 'completed' else None,
                payment_status=payment_status
            )
            bookings_data.append(booking)
        
        self.stdout.write(f'  ✓ Created {len(bookings_data)} bookings')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created bookings data:'))
        self.stdout.write(f'   • {len(created_services)} services')
        self.stdout.write(f'   • {availabilities_created} availability slots')
        self.stdout.write(f'   • {len(bookings_data)} bookings')
