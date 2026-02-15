from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Sum, Avg
from django.utils import timezone
from stats.models import StatisticsCache
from users.models import User
from maintenances.models import Maintenance
from diagnostics.models import Diagnostic
from vehicles.models import Vehicle
from documents.models import Document


class Command(BaseCommand):
    help = 'Seeds the statistics cache table with realistic data'

    def handle(self, *args, **kwargs):
        StatisticsCache.objects.all().delete()
        self.stdout.write('Statistics cache table cleared')

        users = list(
            User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return

        self.stdout.write('\nCreating statistics cache entries...')
        cache_created = 0

        cache_types = ['overview', 'costs', 'maintenance', 'fuel', 'diagnostics']
        today = timezone.now().date()

        for user in users:
            total_vehicles = Vehicle.objects.filter(owner=user).count()
            total_maintenances = Maintenance.objects.filter(created_by=user).count()
            total_diagnostics = Diagnostic.objects.filter(user=user).count()
            total_documents = Document.objects.filter(user=user).count()
            total_spent = Maintenance.objects.filter(created_by=user).aggregate(total=Sum('cost')).get('total') or 0
            average_cost = Maintenance.objects.filter(created_by=user).aggregate(avg=Avg('cost')).get('avg') or 0
            total_spent_value = float(total_spent) if total_spent else 0.0
            average_cost_value = float(average_cost) if average_cost else 0.0

            upcoming_maintenances = Maintenance.objects.filter(
                created_by=user,
                status='SCHEDULED',
                service_date__gte=timezone.now(),
            ).count()

            last_maintenance = Maintenance.objects.filter(created_by=user).order_by('-service_date').first()
            last_maintenance_date = last_maintenance.service_date.date() if last_maintenance else None

            for cache_type in cache_types:
                if cache_type == 'overview':
                    cache_data = {
                        'total_vehicles': total_vehicles,
                        'total_maintenances': total_maintenances,
                        'total_diagnostics': total_diagnostics,
                        'total_documents': total_documents,
                        'total_spent': total_spent_value,
                        'upcoming_maintenances': upcoming_maintenances,
                    }
                elif cache_type == 'costs':
                    cache_data = {
                        'monthly_average': total_spent_value / 6 if total_spent_value else 0,
                        'yearly_total': total_spent_value,
                        'by_category': {
                            'maintenance': total_spent_value,
                            'repairs': total_spent_value * 0.2,
                            'fuel': total_spent_value * 0.35,
                        },
                    }
                elif cache_type == 'maintenance':
                    cache_data = {
                        'completed_count': Maintenance.objects.filter(created_by=user, status='COMPLETED').count(),
                        'upcoming_count': upcoming_maintenances,
                        'overdue_count': Maintenance.objects.filter(
                            created_by=user,
                            status='SCHEDULED',
                            service_date__lt=timezone.now(),
                        ).count(),
                        'average_cost': average_cost_value,
                        'last_maintenance_date': str(last_maintenance_date) if last_maintenance_date else None,
                    }
                elif cache_type == 'fuel':
                    cache_data = {
                        'average_consumption': 7.4,
                        'total_liters': 640,
                        'total_cost': 1020,
                        'trend': 'stable',
                    }
                else:
                    cache_data = {
                        'total_count': total_diagnostics,
                        'issues_found': max(total_diagnostics - 1, 0),
                        'resolved_issues': max(total_diagnostics - 2, 0),
                        'pending_issues': min(total_diagnostics, 2),
                    }

                cache_key = f'{cache_type}_{user.id}_{today.strftime("%Y%m%d")}'
                expires_at = timezone.now() + timedelta(hours=12)

                StatisticsCache.objects.create(
                    user=user,
                    cache_key=cache_key,
                    cache_type=cache_type,
                    data=cache_data,
                    expires_at=expires_at,
                )
                cache_created += 1

        self.stdout.write(f'  ✓ Created {cache_created} cache entries')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {cache_created} statistics cache entries'))
