from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import AIConversation, AIMessage
from .serializers import (
    AIConversationSerializer, AIConversationCreateSerializer,
    AIMessageSerializer, AIMessageCreateSerializer
)
from .ai_service import ai_service
from common.permissions import IsStandardPlan, IsPremiumPlan


class AIConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI conversations
    
    list: Get all conversations for current user
    create: Create a new conversation
    retrieve: Get a specific conversation
    update: Update a conversation
    destroy: Delete a conversation
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter conversations by user"""
        return AIConversation.objects.filter(
            user=self.request.user
        ).prefetch_related('messages')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return AIConversationCreateSerializer
        return AIConversationSerializer
    
    def perform_create(self, serializer):
        """Add current user to conversation"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        conversation = self.get_object()
        
        data = request.data.copy()
        data['conversation'] = conversation.id
        
        serializer = AIMessageCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()
            
            # Update conversation updated_at
            conversation.save()  # This will update updated_at automatically
            
            return Response(AIMessageSerializer(message).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages in a conversation"""
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        serializer = AIMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent conversations"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().order_by('-updated_at')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get conversation statistics"""
        queryset = self.get_queryset()
        
        total_conversations = queryset.count()
        total_messages = AIMessage.objects.filter(
            conversation__user=request.user
        ).count()
        
        return Response({
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'average_messages_per_conversation': round(
                total_messages / total_conversations, 2
            ) if total_conversations > 0 else 0
        })


class AIMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI messages
    
    list: Get all messages for current user's conversations
    create: Create a new message
    retrieve: Get a specific message
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AIMessageSerializer
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        """Filter messages by conversation owner"""
        return AIMessage.objects.filter(
            conversation__user=self.request.user
        ).select_related('conversation')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return AIMessageCreateSerializer
        return AIMessageSerializer


class AIAssistantViewSet(viewsets.ViewSet):
    """
    ViewSet pour les fonctionnalités IA avancées
    Équivalent du AiAssistantController NestJS
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStandardPlan])
    def chat(self, request):
        """
        Chat général avec l'assistant IA - Plan STANDARD minimum
        
        Body: {
            "message": "Votre message",
            "history": [{"role": "user", "content": "..."}, ...]  # optionnel
        }
        """
        message = request.data.get('message')
        history = request.data.get('history', [])
        
        if not message:
            return Response(
                {'error': 'Le message est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            response = ai_service.chat(message, history)
            return Response({
                'content': response['content'],
                'model': response['model']
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStandardPlan])
    def maintenance_suggestions(self, request):
        """
        Obtenir des suggestions de maintenance préventive - Plan STANDARD minimum
        
        Body: {
            "vehicleInfo": {
                "make": "Toyota",
                "model": "Corolla",
                "year": 2020,
                "mileage": 50000
            }
        }
        """
        vehicle_info = request.data.get('vehicleInfo')
        
        if not vehicle_info:
            return Response(
                {'error': 'Les informations du véhicule sont requises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider les champs requis
        required_fields = ['make', 'model', 'year', 'mileage']
        missing_fields = [field for field in required_fields if field not in vehicle_info]
        
        if missing_fields:
            return Response(
                {'error': f'Champs manquants: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            suggestions = ai_service.suggest_preventive_maintenance(vehicle_info)
            
            return Response({
                'vehicleInfo': vehicle_info,
                'suggestions': suggestions,
                'generatedAt': None  # Django sérialisera automatiquement
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsPremiumPlan])
    def diagnostic(self, request):
        """
        Diagnostic d'un problème - Plan PREMIUM minimum
        Nécessite des analyses plus avancées
        
        Body: {
            "symptoms": "Le moteur fait un bruit étrange...",
            "vehicleInfo": {
                "make": "Toyota",
                "model": "Corolla",
                "year": 2020
            }
        }
        """
        symptoms = request.data.get('symptoms')
        vehicle_info = request.data.get('vehicleInfo')
        
        if not symptoms or not vehicle_info:
            return Response(
                {'error': 'Les symptômes et les informations du véhicule sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider les champs requis du véhicule
        required_fields = ['make', 'model', 'year']
        missing_fields = [field for field in required_fields if field not in vehicle_info]
        
        if missing_fields:
            return Response(
                {'error': f'Champs manquants du véhicule: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            diagnosis_result = ai_service.diagnose_problem(symptoms, vehicle_info)
            
            return Response(diagnosis_result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStandardPlan])
    def maintenance_ask(self, request):
        """
        Questions sur la maintenance - Plan STANDARD minimum
        
        Body: {
            "question": "Quand dois-je changer l'huile?",
            "vehicleInfo": {
                "make": "Toyota",
                "model": "Corolla",
                "year": 2020
            },
            "history": [...]  # optionnel
        }
        """
        question = request.data.get('question')
        vehicle_info = request.data.get('vehicleInfo')
        history = request.data.get('history', [])
        
        if not question or not vehicle_info:
            return Response(
                {'error': 'La question et les informations du véhicule sont requises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider les champs requis du véhicule
        required_fields = ['make', 'model', 'year']
        missing_fields = [field for field in required_fields if field not in vehicle_info]
        
        if missing_fields:
            return Response(
                {'error': f'Champs manquants du véhicule: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            answer = ai_service.maintenance_assistant(
                question,
                vehicle_info,
                history
            )
            
            return Response({
                'question': question,
                'answer': answer,
                'vehicleInfo': vehicle_info,
                'timestamp': None  # Django sérialisera automatiquement
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

