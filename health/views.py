from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection
from django.conf import settings
import requests
import redis


class HealthCheckView(APIView):
    """
    Health check général du système
    GET /api/health/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'service': 'autotrack-backend',
            'version': '1.0.0',
            'checks': {}
        }
        
        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            health_status['checks']['database'] = 'ok'
        except Exception as e:
            health_status['checks']['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check Redis (Celery)
        try:
            redis_client = redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            health_status['checks']['redis'] = 'ok'
        except Exception as e:
            health_status['checks']['redis'] = f'error: {str(e)}'
            # Redis is optional, don't mark as unhealthy
        
        return Response(health_status)


class DatabaseHealthView(APIView):
    """
    Health check spécifique pour la base de données
    GET /api/health/db/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
            
            # Get database stats
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
            
            return Response({
                'status': 'healthy',
                'database': 'connected',
                'engine': settings.DATABASES['default']['ENGINE'],
                'stats': {
                    'users': user_count
                }
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class StripeHealthView(APIView):
    """
    Health check pour l'API Stripe
    GET /api/health/stripe/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            stripe_key = settings.STRIPE_SECRET_KEY
            
            if not stripe_key:
                return Response({
                    'status': 'warning',
                    'stripe': 'not_configured',
                    'message': 'Stripe API key not configured'
                })
            
            # Test Stripe API connectivity
            headers = {
                'Authorization': f'Bearer {stripe_key}'
            }
            
            response = requests.get(
                'https://api.stripe.com/v1/charges',
                headers=headers,
                params={'limit': 1},
                timeout=5
            )
            
            if response.status_code == 200:
                return Response({
                    'status': 'healthy',
                    'stripe': 'connected',
                    'api_version': response.headers.get('Stripe-Version', 'unknown')
                })
            else:
                return Response({
                    'status': 'unhealthy',
                    'stripe': 'error',
                    'http_status': response.status_code
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except requests.exceptions.Timeout:
            return Response({
                'status': 'unhealthy',
                'stripe': 'timeout',
                'error': 'Request timeout after 5 seconds'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'stripe': 'error',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class RedisHealthView(APIView):
    """
    Health check pour Redis/Celery
    GET /api/health/redis/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            redis_client = redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            
            # Get Redis info
            info = redis_client.info()
            
            return Response({
                'status': 'healthy',
                'redis': 'connected',
                'version': info.get('redis_version', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0)
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'redis': 'disconnected',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
