from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import Document
from .serializers import (
    DocumentSerializer, DocumentCreateSerializer, DocumentDetailSerializer,
    DocumentUpdateSerializer
)
from .tasks import async_analyze_document, batch_analyze_documents


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents
    
    list: Get all documents for current user
    create: Create a new document (upload file)
    retrieve: Get a specific document
    update: Update a document
    partial_update: Partially update a document
    destroy: Delete a document
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle', 'document_type', 'is_analyzed']
    search_fields = ['title', 'description', 'extracted_text', 'vehicle__make', 'vehicle__model']
    ordering_fields = ['created_at', 'updated_at', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter documents by user"""
        return Document.objects.filter(
            user=self.request.user
        ).select_related('vehicle')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        elif self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentSerializer
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get documents grouped by type"""
        doc_type = request.query_params.get('type')
        
        if doc_type:
            queryset = self.get_queryset().filter(document_type=doc_type)
        else:
            queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unanalyzed(self, request):
        """Get unanalyzed documents"""
        queryset = self.get_queryset().filter(is_analyzed=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get document statistics"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        by_type = queryset.values('document_type').annotate(count=Count('id'))
        
        analyzed = queryset.filter(is_analyzed=True).count()
        unanalyzed = queryset.filter(is_analyzed=False).count()
        
        total_size = sum(doc.file_size for doc in queryset if doc.file_size)
        
        return Response({
            'total_documents': total,
            'by_type': list(by_type),
            'analyzed': analyzed,
            'unanalyzed': unanalyzed,
            'total_storage_bytes': total_size,
            'total_storage_mb': round(total_size / 1024 / 1024, 2) if total_size else 0
        })
    
    @action(detail=False, methods=['get'])
    def by_vehicle(self, request):
        """Get documents grouped by vehicle"""
        vehicle_id = request.query_params.get('vehicle_id')
        
        if vehicle_id:
            queryset = self.get_queryset().filter(vehicle_id=vehicle_id)
        else:
            queryset = self.get_queryset()
        
        # Group by vehicle
        vehicles = {}
        for document in queryset:
            vehicle_key = str(document.vehicle.id)
            if vehicle_key not in vehicles:
                vehicles[vehicle_key] = {
                    'vehicle': {
                        'id': document.vehicle.id,
                        'make': document.vehicle.make,
                        'model': document.vehicle.model,
                        'year': document.vehicle.year
                    },
                    'documents': []
                }
            vehicles[vehicle_key]['documents'].append(
                DocumentSerializer(document, context={'request': request}).data
            )
        
        return Response(list(vehicles.values()))
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyze/extract text from a document using OCR"""
        document = self.get_object()
        
        # Vérifier le type de fichier
        if document.mime_type not in ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']:
            return Response(
                {'error': 'Analysis is only available for images and PDFs.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si le fichier existe
        if not document.file:
            return Response(
                {'error': 'No file attached to this document.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lancer l'analyse asynchrone avec Celery
        task = async_analyze_document.delay(document.id)
        
        return Response({
            'message': 'Document analysis started. Results will be available shortly.',
            'document_id': document.id,
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def batch_analyze(self, request):
        """Analyze multiple documents in batch"""
        document_ids = request.data.get('document_ids', [])
        
        if not document_ids:
            return Response(
                {'error': 'No document IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que tous les documents appartiennent à l'utilisateur
        user_documents = self.get_queryset().filter(id__in=document_ids)
        if user_documents.count() != len(document_ids):
            return Response(
                {'error': 'Some documents not found or not accessible.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lancer l'analyse batch avec Celery
        task = batch_analyze_documents.delay(document_ids)
        
        return Response({
            'message': f'Batch analysis started for {len(document_ids)} documents.',
            'document_count': len(document_ids),
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
