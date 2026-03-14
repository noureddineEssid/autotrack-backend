"""
Service IA pour AutoTrack — Utilise l'agent LangGraph (ReAct) + Capgemini Generative Engine API
"""
from django.conf import settings
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Service d'intelligence artificielle pour l'assistance automobile"""

    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Chat général avec l'IA en maintenant l'historique.

        Args:
            message:              Message de l'utilisateur.
            conversation_history: Historique [{'role': 'user'|'assistant', 'content': '...'}].
            system_prompt:        Prompt système optionnel (surcharge le prompt AutoTrack).
            user_id:              ID utilisateur Django (active les outils DB de l'agent).

        Returns:
            Dict avec 'content' (réponse) et 'model' (modèle utilisé).
        """
        from agents.autotrack_agent import demander

        try:
            response = demander(
                question=message,
                user_id=user_id,
                history=conversation_history or [],
                system_prompt=system_prompt,
            )
            return {
                'content': response,
                'model': getattr(settings, 'AGENT_MODEL', 'anthropic.claude-sonnet-4-6'),
            }
        except Exception as e:
            logger.error(f'Agent error: {str(e)}')
            raise
    
    def suggest_preventive_maintenance(
        self,
        vehicle_info: Dict[str, any]
    ) -> List[str]:
        """
        Suggérer des tâches de maintenance préventive
        
        Args:
            vehicle_info: {make, model, year, mileage}
            
        Returns:
            Liste de suggestions de maintenance
        """
        prompt = f"""Pour un véhicule {vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']} 
avec {vehicle_info['mileage']} km, suggère 5 tâches de maintenance préventive prioritaires.
Retourne une liste numérotée courte et précise."""
        
        try:
            response = self.chat(prompt, [])
            content = response['content']
            
            # Parser les suggestions (lignes numérotées)
            suggestions = []
            for line in content.split('\n'):
                line = line.strip()
                # Chercher lignes comme "1. ...", "1) ...", "- ..."
                if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '1)', '2)', '3)', '4)', '5)', '-', '•']):
                    # Nettoyer la ligne
                    cleaned = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '1)', '2)', '3)', '4)', '5)', '-', '•']:
                        if cleaned.startswith(prefix):
                            cleaned = cleaned[len(prefix):].strip()
                            break
                    if cleaned:
                        suggestions.append(cleaned)
            
            return suggestions[:5]  # Limiter à 5 suggestions
            
        except Exception as e:
            logger.error(f'Error generating maintenance suggestions: {str(e)}')
            return ['Erreur lors de la génération des suggestions. Veuillez réessayer.']
    
    def diagnose_problem(
        self,
        symptoms: str,
        vehicle_info: Dict[str, any]
    ) -> Dict:
        """
        Diagnostiquer un problème de véhicule
        
        Args:
            symptoms: Description des symptômes
            vehicle_info: {make, model, year}
            
        Returns:
            Dict avec diagnosis, urgency, estimated_cost, recommendations
        """
        system_prompt = """Tu es un mécanicien expert. Analyse les symptômes et fournis:
1. Un diagnostic probable
2. Le niveau d'urgence (low/medium/high)
3. Une estimation de coût de réparation en euros
4. Des recommandations pratiques

Réponds en JSON structuré avec les clés: diagnosis, urgency, estimatedCost, recommendations (array)."""
        
        prompt = f"""Véhicule: {vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}
Symptômes: {symptoms}

Analyse et retourne un JSON avec: diagnosis, urgency, estimatedCost, recommendations (array)"""
        
        try:
            response = self.chat(prompt, [], system_prompt)
            content = response['content']
            
            # Extraire le JSON de la réponse
            # Chercher un bloc JSON {...}
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = content[start:end]
                result = json.loads(json_str)
                
                # Valider la structure
                return {
                    'diagnosis': result.get('diagnosis', 'Diagnostic non disponible'),
                    'urgency': result.get('urgency', 'medium'),
                    'estimatedCost': result.get('estimatedCost', 'À déterminer'),
                    'recommendations': result.get('recommendations', ['Consulter un mécanicien'])
                }
            else:
                # Fallback si pas de JSON valide
                return {
                    'diagnosis': content,
                    'urgency': 'medium',
                    'estimatedCost': 'À déterminer',
                    'recommendations': ['Consulter un mécanicien pour un diagnostic précis']
                }
                
        except json.JSONDecodeError:
            # Si le JSON n'est pas valide, retourner le texte brut
            return {
                'diagnosis': response['content'],
                'urgency': 'medium',
                'estimatedCost': 'À déterminer',
                'recommendations': ['Consulter un mécanicien']
            }
        except Exception as e:
            logger.error(f'Error diagnosing problem: {str(e)}')
            raise
    
    def maintenance_assistant(
        self,
        question: str,
        vehicle_info: Dict[str, any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Assistant de maintenance - répond aux questions sur l'entretien
        
        Args:
            question: Question de l'utilisateur
            vehicle_info: {make, model, year}
            conversation_history: Historique de conversation
            
        Returns:
            Réponse de l'assistant
        """
        system_prompt = """Tu es un expert en maintenance automobile. 
Tu aides les utilisateurs avec des conseils sur l'entretien de leur véhicule.
Sois précis, pratique et sécuritaire dans tes recommandations."""
        
        contextual_question = f"""Véhicule: {vehicle_info['year']} {vehicle_info['make']} {vehicle_info['model']}
Question: {question}"""
        
        try:
            response = self.chat(
                contextual_question,
                conversation_history or [],
                system_prompt
            )
            return response['content']
            
        except Exception as e:
            logger.error(f'Error in maintenance assistant: {str(e)}')
            raise


# Instance globale du service
ai_service = AIService()
