from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookEventViewSet, stripe_webhook

app_name = 'webhooks'

router = DefaultRouter()
router.register(r'events', WebhookEventViewSet, basename='webhook-event')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe/', stripe_webhook, name='stripe-webhook'),
]
