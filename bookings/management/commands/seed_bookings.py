from datetime import timedelta, time
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import GarageService, GarageAvailability, Booking, BookingReview
from garages.models import Garage
from users.models import User
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = 'Seeds the bookings table with realistic data'

    def handle(self, *args, **kwargs):
        GarageService.objects.all().delete()
        GarageAvailability.objects.all().delete()
        BookingReview.objects.all().delete()
        Booking.objects.all().delete()
        self.stdout.write('Bookings tables cleared')

        garages = list(Garage.objects.all())
        users = list(
            User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )
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

        self.stdout.write('\nCreating garage services...')
        services_data = [
            {
                'name': 'Vidange moteur',
                'category': 'maintenance',
                'duration_minutes': 45,
                'price': 79.90,
                'description': 'Vidange complete avec changement du filtre a huile',
            },
            {
                'name': 'Revision complete',
                'category': 'maintenance',
                'duration_minutes': 120,
                'price': 249.90,
                'description': 'Revision selon les preconisations constructeur',
            },
            {
                'name': 'Changement plaquettes de frein',
                'category': 'repair',
                'duration_minutes': 90,
                'price': 159.90,
                'description': 'Changement des plaquettes avant ou arriere',
            },
            {
                'name': 'Diagnostic electronique',
                'category': 'diagnostic',
                'duration_minutes': 60,
                'price': 89.90,
                'description': 'Diagnostic complet avec valise electronique',
            },
            {
                'name': 'Changement de pneus',
                'category': 'tire',
                'duration_minutes': 60,
                'price': 45.00,
                'description': 'Montage et equilibrage (prix par pneu)',
            },
            {
                'name': 'Geometrie et parallelisme',
                'category': 'maintenance',
                'duration_minutes': 45,
                'price': 69.90,
                'description': 'Reglage de la geometrie des trains roulants',
            },
            {
                'name': 'Controle technique',
                'category': 'diagnostic',
                'duration_minutes': 30,
                'price': 78.00,
                'description': 'Controle technique reglementaire',
            },
            {
                'name': 'Climatisation',
                'category': 'maintenance',
                'duration_minutes': 90,
                'price': 129.90,
                'description': 'Recharge et desinfection de la climatisation',
            },
        ]

        created_services = []
        for garage in garages:
            for service_data in services_data:
                created_services.append(GarageService.objects.create(garage=garage, **service_data))

        self.stdout.write(f'  ✓ Created {len(created_services)} services')

        self.stdout.write('\nCreating garage availabilities...')
        availabilities_created = 0

        time_slots = [
            (time(8, 0), time(10, 0)),
            (time(10, 0), time(12, 0)),
            (time(14, 0), time(16, 0)),
            (time(16, 0), time(18, 0)),
        ]

        for garage in garages:
            for weekday in range(5):
                for start_time, end_time in time_slots:
                    GarageAvailability.objects.create(
                        garage=garage,
                        weekday=weekday,
                        start_time=start_time,
                        end_time=end_time,
                        max_bookings_per_slot=2,
                    )
                    availabilities_created += 1

            for start_time, end_time in time_slots[:2]:
                GarageAvailability.objects.create(
                    garage=garage,
                    weekday=5,
                    start_time=start_time,
                    end_time=end_time,
                    max_bookings_per_slot=1,
                )
                availabilities_created += 1

        self.stdout.write(f'  ✓ Created {availabilities_created} availability slots')

        self.stdout.write('\nCreating bookings...')
        today = timezone.now().date()
        booking_times = [time(8, 0), time(10, 0), time(14, 0), time(16, 0)]
        notes_list = [
            '',
            'Vehicule qui fait un bruit anormal',
            'Premiere visite',
            'Client regulier',
            'Controle avant depart en vacances',
        ]

        bookings_data = []
        for i in range(24):
            user = users[i % len(users)]
            user_vehicles = [v for v in vehicles if v.owner == user]
            vehicle = user_vehicles[i % len(user_vehicles)] if user_vehicles else vehicles[i % len(vehicles)]
            garage = garages[i % len(garages)]
            service = [s for s in created_services if s.garage == garage][i % len(services_data)]

            booking_date = today + timedelta(days=(i % 14) - 7)
            booking_time = booking_times[i % len(booking_times)]

            if booking_date < today:
                status = 'completed' if i % 3 != 0 else 'cancelled'
                payment_status = 'paid' if status == 'completed' else 'pending'
            elif booking_date == today:
                status = 'confirmed'
                payment_status = 'pending'
            else:
                status = 'pending' if i % 2 == 0 else 'confirmed'
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
                customer_phone=user.phone_number or '+21620000000',
                customer_email=user.email,
                notes=notes_list[i % len(notes_list)],
                estimated_price=service.price,
                final_price=service.price if status == 'completed' else None,
                payment_status=payment_status,
            )
            bookings_data.append(booking)

            if status == 'completed':
                BookingReview.objects.create(
                    booking=booking,
                    rating=4 if i % 2 == 0 else 5,
                    comment='Service rapide et professionnel.',
                    would_recommend=True,
                    service_quality=4,
                    waiting_time=4,
                    value_for_money=5,
                )

        self.stdout.write(f'  ✓ Created {len(bookings_data)} bookings')

        self.stdout.write(self.style.SUCCESS('\n✅ Successfully created bookings data:'))
        self.stdout.write(f'   • {len(created_services)} services')
        self.stdout.write(f'   • {availabilities_created} availability slots')
        self.stdout.write(f'   • {len(bookings_data)} bookings')
