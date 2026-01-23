"""
Statistics Models
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class StatisticsCache(models.Model):
    """
    Cache for frequently requested statistics to improve performance
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stats_cache')
    cache_key = models.CharField(max_length=255, db_index=True)
    cache_type = models.CharField(max_length=50, choices=[
        ('overview', 'Overview'),
        ('costs', 'Costs'),
        ('maintenance', 'Maintenance'),
        ('fuel', 'Fuel'),
        ('diagnostics', 'Diagnostics'),
    ])
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'statistics_cache'
        unique_together = ['user', 'cache_key']
        indexes = [
            models.Index(fields=['user', 'cache_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.cache_type} - {self.cache_key}"
