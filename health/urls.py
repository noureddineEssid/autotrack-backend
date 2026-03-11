from django.urls import path
from .views import (
    HealthCheckView,
    DatabaseHealthView,
    RedisHealthView
)

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health-check'),
    path('db/', DatabaseHealthView.as_view(), name='database-health'),
    path('redis/', RedisHealthView.as_view(), name='redis-health'),
]
