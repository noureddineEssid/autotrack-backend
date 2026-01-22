"""
Tâches Celery pour l'analyse de documents
"""
from celery import shared_task
from .models import Document
from .services.analyzer import document_analyzer
import logging

logger = logging.getLogger(__name__)


@shared_task
def async_analyze_document(document_id: int):
    """
    Analyser un document de manière asynchrone
    
    Args:
        document_id: ID du document à analyser
        
    Returns:
        Résultat de l'analyse
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Vérifier que le fichier existe
        if not document.file:
            logger.error(f"Document {document_id} has no file attached")
            return {'status': 'error', 'message': 'No file attached'}
        
        # Analyser le document
        file_path = document.file.path
        analysis_result = document_analyzer.analyze_document(file_path)
        
        # Mettre à jour le document avec les résultats
        document.extracted_text = analysis_result.get('extracted_text', '')
        document.analysis_data = {
            'document_type': analysis_result.get('document_type'),
            'structured_data': analysis_result.get('structured_data'),
            'confidence': analysis_result.get('confidence'),
            'status': analysis_result.get('status')
        }
        document.save(update_fields=['extracted_text', 'analysis_data'])
        
        logger.info(
            f"Document {document_id} analyzed successfully "
            f"(type: {analysis_result.get('document_type')}, "
            f"confidence: {analysis_result.get('confidence')})"
        )
        
        return {
            'status': 'success',
            'document_id': document_id,
            'document_type': analysis_result.get('document_type'),
            'confidence': analysis_result.get('confidence')
        }
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {'status': 'error', 'message': 'Document not found'}
    except Exception as e:
        logger.error(f"Error analyzing document {document_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def batch_analyze_documents(document_ids: list):
    """
    Analyser plusieurs documents en batch
    
    Args:
        document_ids: Liste des IDs de documents à analyser
        
    Returns:
        Résumé des analyses
    """
    results = {
        'total': len(document_ids),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for doc_id in document_ids:
        result = async_analyze_document(doc_id)
        
        if result.get('status') == 'success':
            results['success'] += 1
        else:
            results['failed'] += 1
        
        results['details'].append({
            'document_id': doc_id,
            'result': result
        })
    
    logger.info(
        f"Batch analysis completed: {results['success']} success, "
        f"{results['failed']} failed out of {results['total']}"
    )
    
    return results
