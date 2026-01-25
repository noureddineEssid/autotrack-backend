from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from stats.models import StatisticsCache
from users.models import User
import random


class Command(BaseCommand):
    help = 'Seeds the statistics cache table with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer le cache existant
        StatisticsCache.objects.all().delete()
        self.stdout.write('Statistics cache table cleared')
        
        users = list(User.objects.all())
        
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return
        
        # Créer les entrées de cache
        self.stdout.write('\nCreating statistics cache entries...')
        cache_created = 0
        
        cache_types = ['overview', 'costs', 'maintenance', 'fuel', 'diagnostics']
        
        for user in users:
            for cache_type in cache_types:
                # Créer des données de cache selon le type
                cache_data = {}
                
                if cache_type == 'overview':
                    cache_data = {
                        'total_vehicles': random.randint(1, 5),
                        'total_maintenances': random.randint(5, 30),
                        'total_diagnostics': random.randint(2, 15),
                        'total_spent': round(random.uniform(1000, 5000), 2),
                        'upcoming_maintenances': random.randint(0, 5),
                    }
                elif cache_type == 'costs':
                    cache_data = {
                        'monthly_average': round(random.uniform(100, 400), 2),
                        'yearly_total': round(random.uniform(1500, 4500), 2),
                        'by_category': {
                            'maintenance': round(random.uniform(500, 1500), 2),
                            'repairs': round(random.uniform(300, 1000), 2),
                            'fuel': round(random.uniform(800, 2000), 2),
                        }
                    }
                elif cache_type == 'maintenance':
                    cache_data = {
                        'completed_count': random.randint(10, 50),
                        'upcoming_count': random.randint(0, 5),
                        'overdue_count': random.randint(0, 3),
                        'average_cost': round(random.uniform(100, 300), 2),
                        'last_maintenance_date': str(timezone.now().date() - timedelta(days=random.randint(1, 90))),
                    }
                elif cache_type == 'fuel':
                    cache_data = {
                        'average_consumption': round(random.uniform(6, 10), 2),
                        'total_liters': round(random.uniform(500, 2000), 2),
                        'total_cost': round(random.uniform(800, 3000), 2),
                        'trend': random.choice(['increasing', 'decreasing', 'stable']),
                    }
                elif cache_type == 'diagnostics':
                    cache_data = {
                        'total_count': random.randint(5, 20),
                        'issues_found': random.randint(2, 10),
                        'resolved_issues': random.randint(1, 8),
                        'pending_issues': random.randint(0, 3),
                    }
                
                # Créer l'entrée de cache
                cache_key = f'{cache_type}_{user.id}_{timezone.now().strftime("%Y%m%d")}'
                expires_at = timezone.now() + timedelta(hours=random.randint(6, 24))
                
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
