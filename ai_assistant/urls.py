from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIConversationViewSet, AIMessageViewSet, AIAssistantViewSet

app_name = 'ai_assistant'

router = DefaultRouter()
router.register(r'conversations', AIConversationViewSet, basename='conversation')
router.register(r'messages', AIMessageViewSet, basename='message')
router.register(r'assistant', AIAssistantViewSet, basename='assistant')

urlpatterns = [
    path('', include(router.urls)),
]
