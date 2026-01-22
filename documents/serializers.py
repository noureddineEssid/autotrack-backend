from rest_framework import serializers
from .models import Document
from vehicles.serializers import VehicleSerializer


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer"""
    
    vehicle_info = VehicleSerializer(source='vehicle', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'user', 'vehicle', 'vehicle_info', 'document_type', 'title',
            'description', 'file', 'file_url', 'file_size', 'mime_type',
            'extracted_text', 'analysis_data', 'is_analyzed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'file_size', 'mime_type', 'extracted_text', 
                            'analysis_data', 'is_analyzed', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Document creation serializer"""
    
    class Meta:
        model = Document
        fields = ['vehicle', 'document_type', 'title', 'description', 'file']
    
    def validate(self, data):
        # Vérifie que le véhicule appartient à l'utilisateur
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            vehicle = data.get('vehicle')
            if vehicle and vehicle.owner != request.user:
                raise serializers.ValidationError({
                    'vehicle': 'You can only create documents for your own vehicles.'
                })
        
        # Validation du fichier
        file = data.get('file')
        if file:
            # Limite de taille: 10MB
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise serializers.ValidationError({
                    'file': f'File size must not exceed {max_size / 1024 / 1024}MB.'
                })
            
            # Types MIME autorisés
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ]
            
            if file.content_type not in allowed_types:
                raise serializers.ValidationError({
                    'file': f'File type {file.content_type} is not allowed. Allowed types: PDF, JPEG, PNG, GIF, DOC, DOCX.'
                })
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        file = validated_data.get('file')
        
        # Enregistrer la taille et le type MIME
        if file:
            validated_data['file_size'] = file.size
            validated_data['mime_type'] = file.content_type
        
        document = super().create(validated_data)
        
        # TODO: Trigger OCR processing asynchronously via Celery for images and PDFs
        # from documents.tasks import process_document_ocr
        # if document.mime_type in ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']:
        #     process_document_ocr.delay(document.id)
        
        return document


class DocumentDetailSerializer(DocumentSerializer):
    """Document detail serializer with extracted text"""
    
    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Document update serializer"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'title', 'description', 'file']
    
    def validate(self, data):
        # Validation du fichier si présent
        file = data.get('file')
        if file:
            # Limite de taille: 10MB
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise serializers.ValidationError({
                    'file': f'File size must not exceed {max_size / 1024 / 1024}MB.'
                })
            
            # Types MIME autorisés
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            ]
            
            if file.content_type not in allowed_types:
                raise serializers.ValidationError({
                    'file': f'File type {file.content_type} is not allowed. Allowed types: PDF, JPEG, PNG, GIF, DOC, DOCX.'
                })
        
        return data
    
    def update(self, instance, validated_data):
        file = validated_data.get('file')
        
        # Mettre à jour la taille et le type MIME si nouveau fichier
        if file:
            validated_data['file_size'] = file.size
            validated_data['mime_type'] = file.content_type
            
            # Reset analysis if file changed
            validated_data['extracted_text'] = None
            validated_data['analysis_data'] = {}
            validated_data['is_analyzed'] = False
        
        document = super().update(instance, validated_data)
        
        # TODO: Trigger OCR processing if file changed
        # from documents.tasks import process_document_ocr
        # if file and document.mime_type in ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']:
        #     process_document_ocr.delay(document.id)
        
        return document
