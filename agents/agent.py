#!/usr/bin/env python3
"""
Mon Agent IA — Agent conversationnel avec outils
Basé sur LangGraph (ReAct) + Capgemini Generative Engine API (OpenAI-compatible)

Usage :
    python agent.py
"""

import os
import ast
import operator as op
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

# ─── Configuration ────────────────────────────────────────────────────────────

API_KEY = os.environ.get("GEP_API_KEY", "0htw69JBnB7CovHcukwKV8k0Ba0oq0Vf2NtzWM3a")
BASE_URL = "https://openai.generative.engine.capgemini.com/v1"
MODEL_NAME = os.environ.get("AGENT_MODEL", "anthropic.claude-sonnet-4-6")

if not API_KEY:
    raise EnvironmentError(
        "La variable d'environnement GEP_API_KEY n'est pas définie.\n"
        "Exécutez : export GEP_API_KEY=votre_cle_api"
    )

# ─── LLM ──────────────────────────────────────────────────────────────────────

llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0,
)

# ─── Outils ───────────────────────────────────────────────────────────────────

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
    """Évalue récursivement un nœud AST (sans recourir à eval)."""
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


@tool
def calculer(expression: str) -> str:
    """
    Évalue une expression mathématique (ex: '(12 + 8) * 3 / 2').
    Opérateurs supportés : +, -, *, /, **, %, //.
    N'utilise pas eval — protection contre les injections de code.
    """
    try:
        arbre = ast.parse(expression.strip(), mode="eval")
        return str(_evaluer(arbre.body))
    except ZeroDivisionError:
        return "Erreur : division par zéro."
    except (ValueError, KeyError) as e:
        return f"Erreur : expression non supportée — {e}"
    except SyntaxError as e:
        return f"Erreur de syntaxe : {e}"
    except Exception as e:
        return f"Erreur inattendue : {e}"


@tool
def date_heure_actuelle() -> str:
    """Retourne la date et l'heure actuelles du système."""
    return datetime.now().strftime("Le %A %d %B %Y à %H:%M:%S")


@tool
def lire_fichier(chemin: str) -> str:
    """
    Lit et retourne le contenu d'un fichier texte local.
    Paramètre chemin : chemin absolu ou relatif vers le fichier.
    Tronqué à 5000 caractères si le fichier est trop grand.
    """
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
        if len(contenu) > 5000:
            return contenu[:5000] + "\n\n[... tronqué à 5000 caractères ...]"
        return contenu
    except FileNotFoundError:
        return f"Erreur : fichier '{chemin}' introuvable."
    except PermissionError:
        return f"Erreur : permission refusée pour '{chemin}'."
    except UnicodeDecodeError:
        return f"Erreur : '{chemin}' n'est pas un fichier texte valide."
    except Exception as e:
        return f"Erreur : {e}"


# ─── Agent ReAct ──────────────────────────────────────────────────────────────

OUTILS = [calculer, date_heure_actuelle, lire_fichier]

SYSTEME = (
    "Tu es un assistant IA utile, précis et concis. "
    "Utilise les outils disponibles quand c'est nécessaire. "
    "Réponds toujours dans la même langue que l'utilisateur."
)

agent = create_react_agent(llm, OUTILS)


def demander(question: str) -> str:
    """Envoie une question à l'agent et retourne sa réponse."""
    resultat = agent.invoke({
        "messages": [
            SystemMessage(content=SYSTEME),
            ("human", question),
        ]
    })
    return resultat["messages"][-1].content


# ─── Interface console ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(f"    Mon Agent IA  (modèle : {MODEL_NAME})")
    print("    Tapez 'quit' ou 'exit' pour quitter")
    print("=" * 60)
    print()

    while True:
        try:
            entree = input("Vous : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break

        if not entree:
            continue

        if entree.lower() in {"quit", "exit", "q", "au revoir", "bye"}:
            print("Au revoir !")
            break

        try:
            reponse = demander(entree)
            print(f"\nAgent : {reponse}\n")
        except Exception as e:
            print(f"\nErreur : {e}\n")
