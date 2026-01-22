"""
Service d'analyse de documents avec OCR
"""
import pytesseract
from PIL import Image
import json
import re
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """Service d'analyse de documents avec OCR et détection de type"""
    
    # Types de documents supportés
    DOCUMENT_TYPES = {
        'invoice': 'Facture',
        'registration': 'Carte Grise',
        'insurance': 'Attestation d\'Assurance',
        'maintenance': 'Facture Entretien',
        'receipt': 'Reçu',
        'contract': 'Contrat',
        'other': 'Autre'
    }
    
    def __init__(self):
        """Initialiser l'analyseur"""
        self.tesseract_config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Seg Mode 6
    
    def analyze_document(self, file_path: str) -> Dict:
        """
        Analyser un document complet
        
        Args:
            file_path: Chemin vers le fichier image
            
        Returns:
            Dict avec: extracted_text, document_type, structured_data, confidence
        """
        try:
            # 1. Extraire le texte avec OCR
            extracted_text = self.extract_text(file_path)
            
            # 2. Détecter le type de document
            document_type = self.detect_document_type(extracted_text)
            
            # 3. Parser les données structurées selon le type
            structured_data = self.parse_structured_data(extracted_text, document_type)
            
            # 4. Calculer la confiance de l'analyse
            confidence = self.calculate_confidence(extracted_text, structured_data)
            
            return {
                'extracted_text': extracted_text,
                'document_type': document_type,
                'structured_data': structured_data,
                'confidence': confidence,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document {file_path}: {str(e)}")
            return {
                'extracted_text': '',
                'document_type': 'other',
                'structured_data': {},
                'confidence': 0.0,
                'status': 'error',
                'error_message': str(e)
            }
    
    def extract_text(self, file_path: str) -> str:
        """
        Extraire le texte d'une image avec pytesseract
        
        Args:
            file_path: Chemin vers le fichier image
            
        Returns:
            Texte extrait
        """
        try:
            # Ouvrir l'image
            image = Image.open(file_path)
            
            # Convertir en RGB si nécessaire
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extraire le texte avec Tesseract
            text = pytesseract.image_to_string(
                image,
                lang='fra+eng',  # Français + Anglais
                config=self.tesseract_config
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def detect_document_type(self, text: str) -> str:
        """
        Détecter le type de document basé sur le texte extrait
        
        Args:
            text: Texte extrait du document
            
        Returns:
            Type de document détecté
        """
        text_lower = text.lower()
        
        # Patterns pour identifier les types de documents
        patterns = {
            'invoice': [
                r'facture',
                r'invoice',
                r'montant\s+ttc',
                r'total\s+ttc',
                r'n[°o]\s*facture'
            ],
            'registration': [
                r'carte\s+grise',
                r'certificat\s+d[\']immatriculation',
                r'immatriculation',
                r'marque\s+:',
                r'modèle\s+:'
            ],
            'insurance': [
                r'attestation\s+d[\']assurance',
                r'contrat\s+d[\']assurance',
                r'assureur',
                r'police\s+d[\']assurance',
                r'numéro\s+de\s+contrat'
            ],
            'maintenance': [
                r'entretien',
                r'révision',
                r'maintenance',
                r'vidange',
                r'pneus',
                r'garage'
            ],
            'receipt': [
                r'reçu',
                r'ticket',
                r'caisse',
                r'merci\s+de\s+votre\s+visite'
            ],
            'contract': [
                r'contrat',
                r'convention',
                r'signataire',
                r'article\s+\d+'
            ]
        }
        
        # Compter les matches pour chaque type
        scores = {}
        for doc_type, type_patterns in patterns.items():
            score = 0
            for pattern in type_patterns:
                if re.search(pattern, text_lower):
                    score += 1
            scores[doc_type] = score
        
        # Retourner le type avec le meilleur score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'other'
    
    def parse_structured_data(self, text: str, document_type: str) -> Dict:
        """
        Parser les données structurées selon le type de document
        
        Args:
            text: Texte extrait
            document_type: Type de document détecté
            
        Returns:
            Données structurées extraites
        """
        data = {}
        
        if document_type == 'invoice':
            data = self._parse_invoice(text)
        elif document_type == 'registration':
            data = self._parse_registration(text)
        elif document_type == 'insurance':
            data = self._parse_insurance(text)
        elif document_type == 'maintenance':
            data = self._parse_maintenance(text)
        
        return data
    
    def _parse_invoice(self, text: str) -> Dict:
        """Parser une facture"""
        data = {}
        
        # Numéro de facture
        invoice_number = re.search(r'n[°o]\s*facture\s*:?\s*(\w+)', text, re.IGNORECASE)
        if invoice_number:
            data['invoice_number'] = invoice_number.group(1)
        
        # Date
        date_pattern = re.search(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})', text)
        if date_pattern:
            data['date'] = date_pattern.group(1)
        
        # Montant total
        amount_pattern = re.search(r'total\s+ttc\s*:?\s*([\d\s]+[,.]?\d*)\s*€?', text, re.IGNORECASE)
        if amount_pattern:
            data['total_amount'] = amount_pattern.group(1).strip()
        
        return data
    
    def _parse_registration(self, text: str) -> Dict:
        """Parser une carte grise"""
        data = {}
        
        # Immatriculation
        plate_pattern = re.search(r'([A-Z]{2}[-\s]?\d{3}[-\s]?[A-Z]{2})', text)
        if plate_pattern:
            data['license_plate'] = plate_pattern.group(1)
        
        # Marque
        brand_pattern = re.search(r'marque\s*:?\s*([A-Z\s]+)', text, re.IGNORECASE)
        if brand_pattern:
            data['brand'] = brand_pattern.group(1).strip()
        
        # Modèle
        model_pattern = re.search(r'modèle\s*:?\s*([A-Z0-9\s]+)', text, re.IGNORECASE)
        if model_pattern:
            data['model'] = model_pattern.group(1).strip()
        
        return data
    
    def _parse_insurance(self, text: str) -> Dict:
        """Parser une attestation d'assurance"""
        data = {}
        
        # Numéro de contrat
        contract_pattern = re.search(r'n[°o]\s*contrat\s*:?\s*(\w+)', text, re.IGNORECASE)
        if contract_pattern:
            data['contract_number'] = contract_pattern.group(1)
        
        # Assureur
        insurer_pattern = re.search(r'assureur\s*:?\s*([A-Z\s]+)', text, re.IGNORECASE)
        if insurer_pattern:
            data['insurer'] = insurer_pattern.group(1).strip()
        
        return data
    
    def _parse_maintenance(self, text: str) -> Dict:
        """Parser une facture d'entretien"""
        data = {}
        
        # Chercher types de services
        services = []
        if re.search(r'vidange', text, re.IGNORECASE):
            services.append('Vidange')
        if re.search(r'pneus', text, re.IGNORECASE):
            services.append('Pneus')
        if re.search(r'révision', text, re.IGNORECASE):
            services.append('Révision')
        
        if services:
            data['services'] = services
        
        # Kilométrage
        mileage_pattern = re.search(r'(\d{1,3}[\s\.]?\d{3})\s*km', text, re.IGNORECASE)
        if mileage_pattern:
            data['mileage'] = mileage_pattern.group(1).replace(' ', '').replace('.', '')
        
        return data
    
    def calculate_confidence(self, text: str, structured_data: Dict) -> float:
        """
        Calculer le niveau de confiance de l'analyse
        
        Args:
            text: Texte extrait
            structured_data: Données structurées extraites
            
        Returns:
            Score de confiance entre 0.0 et 1.0
        """
        confidence = 0.0
        
        # Base: texte non vide
        if text:
            confidence += 0.3
        
        # Texte de longueur raisonnable
        if len(text) > 50:
            confidence += 0.2
        
        # Données structurées extraites
        data_count = len(structured_data)
        if data_count > 0:
            confidence += min(0.5, data_count * 0.1)
        
        return min(1.0, confidence)


# Instance globale
document_analyzer = DocumentAnalyzer()
