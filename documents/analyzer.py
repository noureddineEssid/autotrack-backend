"""
Service d'analyse OCR pour les documents AutoTrack
Extrait le texte et les données structurées des images de documents
"""
import pytesseract
from PIL import Image
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentAnalyzerService:
    """
    Service d'analyse de documents avec OCR
    Extrait des informations utiles des documents scannés
    """
    
    @staticmethod
    def extract_text_from_image(image_path):
        """
        Extrait le texte brut d'une image
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            str: Texte extrait
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='fra+eng')
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            return ""
    
    @staticmethod
    def analyze_vehicle_registration(image_path):
        """
        Analyse une carte grise et extrait les informations clés
        
        Returns:
            dict: Informations extraites (immatriculation, marque, modèle, etc.)
        """
        text = DocumentAnalyzerService.extract_text_from_image(image_path)
        
        data = {
            'document_type': 'registration',
            'registration_number': None,
            'brand': None,
            'model': None,
            'vin': None,
            'first_registration_date': None,
            'raw_text': text
        }
        
        # Extraction du numéro d'immatriculation (format français AA-123-BB)
        registration_match = re.search(r'[A-Z]{2}-\d{3}-[A-Z]{2}', text)
        if registration_match:
            data['registration_number'] = registration_match.group()
        
        # Extraction du VIN (17 caractères alphanumériques)
        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)
        if vin_match:
            data['vin'] = vin_match.group()
        
        # Extraction de la date (format DD/MM/YYYY)
        date_match = re.search(r'\b(\d{2})/(\d{2})/(\d{4})\b', text)
        if date_match:
            try:
                data['first_registration_date'] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
            except:
                pass
        
        # Recherche de marques courantes
        common_brands = [
            'RENAULT', 'PEUGEOT', 'CITROËN', 'CITROEN', 'VOLKSWAGEN', 'BMW', 
            'MERCEDES', 'AUDI', 'TOYOTA', 'NISSAN', 'FORD', 'OPEL',
            'FIAT', 'SEAT', 'SKODA', 'HYUNDAI', 'KIA', 'MAZDA'
        ]
        
        text_upper = text.upper()
        for brand in common_brands:
            if brand in text_upper:
                data['brand'] = brand.capitalize()
                break
        
        return data
    
    @staticmethod
    def analyze_invoice(image_path):
        """
        Analyse une facture et extrait les informations clés
        
        Returns:
            dict: Informations extraites (montant, date, garage, etc.)
        """
        text = DocumentAnalyzerService.extract_text_from_image(image_path)
        
        data = {
            'document_type': 'invoice',
            'amount': None,
            'date': None,
            'invoice_number': None,
            'garage_name': None,
            'raw_text': text
        }
        
        # Extraction du montant (format français: 123,45 € ou 123.45 EUR)
        amount_patterns = [
            r'(?:Total|TOTAL|Montant|MONTANT)[\s:]*(\d+[,\.]\d{2})\s*€',
            r'(\d+[,\.]\d{2})\s*(?:EUR|€)',
            r'Total[\s:]+(\d+[,\.]\d{2})'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    data['amount'] = float(amount_str)
                    break
                except:
                    pass
        
        # Extraction de la date
        date_match = re.search(r'\b(\d{2})/(\d{2})/(\d{4})\b', text)
        if date_match:
            try:
                data['date'] = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
            except:
                pass
        
        # Extraction du numéro de facture
        invoice_patterns = [
            r'(?:Facture|FACTURE|Invoice|N°)[\s:]+([A-Z0-9\-]+)',
            r'(?:Fact|FACT)[\s:]+([0-9]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text)
            if match:
                data['invoice_number'] = match.group(1)
                break
        
        # Essayer d'extraire le nom du garage (première ligne souvent)
        lines = text.split('\n')
        for line in lines[:5]:  # Chercher dans les 5 premières lignes
            line = line.strip()
            if len(line) > 5 and not line.isdigit():
                data['garage_name'] = line
                break
        
        return data
    
    @staticmethod
    def analyze_insurance(image_path):
        """
        Analyse une carte verte d'assurance
        
        Returns:
            dict: Informations extraites
        """
        text = DocumentAnalyzerService.extract_text_from_image(image_path)
        
        data = {
            'document_type': 'insurance',
            'policy_number': None,
            'expiry_date': None,
            'insurance_company': None,
            'raw_text': text
        }
        
        # Extraction du numéro de police
        policy_match = re.search(r'(?:Police|Contrat|N°)[\s:]+([A-Z0-9]+)', text)
        if policy_match:
            data['policy_number'] = policy_match.group(1)
        
        # Extraction de la date d'expiration
        date_patterns = [
            r'(?:Expir|Valable jusqu|Validité).*?(\d{2})/(\d{2})/(\d{4})',
            r'(\d{2})/(\d{2})/(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    data['expiry_date'] = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
                    break
                except:
                    pass
        
        # Compagnies d'assurance courantes
        insurance_companies = [
            'AXA', 'MAAF', 'MACIF', 'MAIF', 'GROUPAMA', 'MMA', 
            'ALLIANZ', 'GENERALI', 'MATMUT', 'GMF', 'DIRECT ASSURANCE'
        ]
        
        text_upper = text.upper()
        for company in insurance_companies:
            if company in text_upper:
                data['insurance_company'] = company
                break
        
        return data
    
    @staticmethod
    def analyze_document(image_path, document_type=None):
        """
        Analyse un document et retourne les données extraites
        
        Args:
            image_path: Chemin vers l'image
            document_type: Type de document ('registration', 'invoice', 'insurance')
            
        Returns:
            dict: Données extraites selon le type de document
        """
        try:
            # Si le type est spécifié, utiliser l'analyseur approprié
            if document_type == 'registration':
                return DocumentAnalyzerService.analyze_vehicle_registration(image_path)
            elif document_type == 'invoice':
                return DocumentAnalyzerService.analyze_invoice(image_path)
            elif document_type == 'insurance':
                return DocumentAnalyzerService.analyze_insurance(image_path)
            else:
                # Analyse générique
                text = DocumentAnalyzerService.extract_text_from_image(image_path)
                return {
                    'document_type': 'generic',
                    'raw_text': text,
                    'analyzed': True
                }
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            return {
                'error': str(e),
                'analyzed': False
            }
