"""
AutoTrack Agent IA — Agent LangGraph (ReAct) spécialisé automobile
Capgemini Generative Engine API (OpenAI-compatible)
"""
import ast
import operator as op
from datetime import datetime
from typing import Optional, List, Dict

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent


# ─── LLM (initialisation lazy, une seule instance) ────────────────────────────

_llm: Optional[ChatOpenAI] = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        from django.conf import settings
        _llm = ChatOpenAI(
            model=getattr(settings, 'AGENT_MODEL', 'anthropic.claude-sonnet-4-6'),
            base_url="https://openai.generative.engine.capgemini.com/v1",
            api_key=settings.GEP_API_KEY,
            temperature=0,
        )
    return _llm


# ─── Calcul sécurisé (sans eval) ──────────────────────────────────────────────

_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
    ast.USub: op.neg,
}


def _evaluer(noeud):
    if isinstance(noeud, ast.Constant):
        return noeud.value
    if isinstance(noeud, ast.BinOp):
        fn = _OPS.get(type(noeud.op))
        if fn is None:
            raise ValueError(f"Opérateur non supporté : {type(noeud.op).__name__}")
        return fn(_evaluer(noeud.left), _evaluer(noeud.right))
    if isinstance(noeud, ast.UnaryOp):
        fn = _OPS.get(type(noeud.op))
        if fn is None:
            raise ValueError(f"Opérateur non supporté : {type(noeud.op).__name__}")
        return fn(_evaluer(noeud.operand))
    raise ValueError(f"Expression non supportée : {ast.dump(noeud)}")


# ─── Outils de l'agent ────────────────────────────────────────────────────────

@tool
def calculer(expression: str) -> str:
    """
    Évalue une expression mathématique (ex: '(12 + 8) * 3 / 2').
    Opérateurs supportés : +, -, *, /, **, %, //.
    """
    try:
        arbre = ast.parse(expression.strip(), mode="eval")
        return str(_evaluer(arbre.body))
    except ZeroDivisionError:
        return "Erreur : division par zéro."
    except (ValueError, SyntaxError) as e:
        return f"Erreur : {e}"
    except Exception as e:
        return f"Erreur inattendue : {e}"


@tool
def date_heure_actuelle() -> str:
    """Retourne la date et l'heure actuelles du système."""
    return datetime.now().strftime("Le %A %d %B %Y à %H:%M:%S")


@tool
def lister_vehicules(user_id: int) -> str:
    """
    Liste les véhicules enregistrés d'un utilisateur AutoTrack.
    Paramètre : user_id — l'identifiant (entier) de l'utilisateur connecté.
    """
    from vehicles.models import Vehicle
    vehicules = list(
        Vehicle.objects.filter(owner_id=user_id).values(
            'id', 'make', 'model', 'year', 'mileage', 'fuel_type',
            'license_plate', 'color', 'transmission',
        )
    )
    if not vehicules:
        return "Aucun véhicule enregistré pour cet utilisateur."
    lines = [f"{len(vehicules)} véhicule(s) enregistré(s) :"]
    for v in vehicules:
        lines.append(
            f"- [ID:{v['id']}] {v['make']} {v['model']} ({v['year']}) | "
            f"{v.get('mileage') or 'N/A'} km | {v.get('fuel_type') or 'N/A'} | "
            f"Boîte : {v.get('transmission') or 'N/A'} | "
            f"Plaque : {v.get('license_plate') or 'N/A'} | "
            f"Couleur : {v.get('color') or 'N/A'}"
        )
    return "\n".join(lines)


@tool
def historique_maintenances(vehicle_id: int) -> str:
    """
    Retourne les 10 dernières maintenances d'un véhicule AutoTrack.
    Paramètre : vehicle_id — l'identifiant (entier) du véhicule.
    """
    from maintenances.models import Maintenance
    maintenances = list(
        Maintenance.objects.filter(vehicle_id=vehicle_id)
        .order_by('-service_date')
        .values('service_type', 'service_date', 'mileage', 'cost', 'status', 'description')[:10]
    )
    if not maintenances:
        return f"Aucune maintenance enregistrée pour le véhicule ID {vehicle_id}."
    lines = [f"10 dernières maintenances du véhicule ID {vehicle_id} :"]
    for m in maintenances:
        date = m['service_date'].strftime('%d/%m/%Y') if m['service_date'] else 'N/A'
        cost = f"{m['cost']} €" if m['cost'] else 'N/A'
        desc = f" — {m['description']}" if m.get('description') else ''
        lines.append(
            f"- {date} | {m['service_type']}{desc} | "
            f"{m.get('mileage') or 'N/A'} km | {cost} | {m['status']}"
        )
    return "\n".join(lines)


# ─── Prompt système AutoTrack ─────────────────────────────────────────────────

SYSTEME_AUTOTRACK = (
    "Tu es AutoAssist, l'assistant IA intelligent d'AutoTrack, spécialisé dans la gestion automobile.\n"
    "Tu aides les utilisateurs à :\n"
    "- Consulter et gérer leurs véhicules enregistrés\n"
    "- Suivre et analyser leur historique de maintenance\n"
    "- Planifier des entretiens préventifs\n"
    "- Diagnostiquer des problèmes mécaniques\n"
    "- Répondre à toutes questions concernant l'automobile\n\n"
    "Utilise les outils disponibles pour accéder aux données réelles de l'utilisateur.\n"
    "Réponds toujours dans la langue de l'utilisateur. Sois précis, utile et concis."
)

OUTILS = [calculer, date_heure_actuelle, lister_vehicules, historique_maintenances]


# ─── Agent (singleton lazy) ────────────────────────────────────────────────────

_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = create_react_agent(_get_llm(), OUTILS)
    return _agent


# ─── Point d'entrée principal ──────────────────────────────────────────────────

def demander(
    question: str,
    user_id: Optional[int] = None,
    history: Optional[List[Dict]] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Envoie une question à l'agent AutoTrack et retourne la réponse.

    Args:
        question:      Message de l'utilisateur.
        user_id:       ID de l'utilisateur Django (active les outils DB).
        history:       Historique de conversation
                       [{'role': 'user'|'assistant', 'content': '...'}].
        system_prompt: Surcharge optionnelle du prompt système AutoTrack.

    Returns:
        Réponse textuelle de l'agent.
    """
    messages = []

    # Prompt système (AutoTrack par défaut ou surcharge)
    messages.append(SystemMessage(content=system_prompt or SYSTEME_AUTOTRACK))

    # Injecter l'ID utilisateur pour les outils DB
    if user_id is not None:
        messages.append(SystemMessage(content=f"ID de l'utilisateur connecté : {user_id}"))

    # Historique de conversation
    for msg in (history or []):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'user':
            messages.append(HumanMessage(content=content))
        elif role in ('assistant', 'ai'):
            messages.append(AIMessage(content=content))

    # Question courante
    messages.append(HumanMessage(content=question))

    result = _get_agent().invoke({"messages": messages})
    return result["messages"][-1].content
