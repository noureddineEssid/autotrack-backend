from typing import Dict, List


PLAN_CATALOG: Dict[str, dict] = {
    "free": {
        "_id": "free",
        "type": "free",
        "name": "Gratuit",
        "description": "Pour démarrer et découvrir AutoTrack+.",
        "monthlyPrice": 0,
        "yearlyPrice": 0,
        "currency": "EUR",
        "yearlyDiscount": 0,
        "isPopular": False,
        "badge": "Essentiel",
        "colorAccent": "#64748B",
        "highlights": [
            "Jusqu’à 3 véhicules",
            "Stockage 200 Mo",
            "Diagnostics limités",
        ],
        "features": [
            "Gestion de véhicules",
            "Rappels d’entretien",
            "Documents essentiels",
        ],
        "featuresByCategory": {
            "Gestion": {
                "name": "Gestion",
                "features": [
                    {
                        "key": "vehicles",
                        "label": "Véhicules",
                        "type": "limit",
                        "value": 3,
                        "displayValue": "3 véhicules",
                    },
                    {
                        "key": "documents",
                        "label": "Documents",
                        "type": "limit",
                        "value": 50,
                        "displayValue": "50 documents",
                    },
                ],
            },
            "Suivi": {
                "name": "Suivi",
                "features": [
                    {
                        "key": "maintenances",
                        "label": "Maintenances/mois",
                        "type": "limit",
                        "value": 10,
                        "displayValue": "10 / mois",
                    },
                    {
                        "key": "diagnostics",
                        "label": "Diagnostics/mois",
                        "type": "limit",
                        "value": 5,
                        "displayValue": "5 / mois",
                    },
                ],
            },
            "Stockage": {
                "name": "Stockage",
                "features": [
                    {
                        "key": "storage",
                        "label": "Stockage",
                        "type": "limit",
                        "value": 200,
                        "displayValue": "200 Mo",
                    }
                ],
            },
        },
        "limits": {
            "vehicles": 3,
            "documents": 50,
            "maintenances": 10,
            "diagnostics": 5,
            "storage_mb": 200,
        },
    },
    "standard": {
        "_id": "standard",
        "type": "standard",
        "name": "Standard",
        "description": "Idéal pour une utilisation régulière.",
        "monthlyPrice": 9.99,
        "yearlyPrice": 99.0,
        "currency": "EUR",
        "yearlyDiscount": 17,
        "isPopular": True,
        "badge": "Le plus populaire",
        "colorAccent": "#2563EB",
        "highlights": [
            "Jusqu’à 10 véhicules",
            "Stockage 1 Go",
            "Rapports avancés",
        ],
        "features": [
            "Tout le plan Gratuit",
            "Diagnostics avancés",
            "Support prioritaire",
        ],
        "featuresByCategory": {
            "Gestion": {
                "name": "Gestion",
                "features": [
                    {
                        "key": "vehicles",
                        "label": "Véhicules",
                        "type": "limit",
                        "value": 10,
                        "displayValue": "10 véhicules",
                    },
                    {
                        "key": "documents",
                        "label": "Documents",
                        "type": "limit",
                        "value": 200,
                        "displayValue": "200 documents",
                    },
                ],
            },
            "Suivi": {
                "name": "Suivi",
                "features": [
                    {
                        "key": "maintenances",
                        "label": "Maintenances/mois",
                        "type": "limit",
                        "value": 50,
                        "displayValue": "50 / mois",
                    },
                    {
                        "key": "diagnostics",
                        "label": "Diagnostics/mois",
                        "type": "limit",
                        "value": 30,
                        "displayValue": "30 / mois",
                    },
                ],
            },
            "Stockage": {
                "name": "Stockage",
                "features": [
                    {
                        "key": "storage",
                        "label": "Stockage",
                        "type": "limit",
                        "value": 1024,
                        "displayValue": "1 Go",
                    }
                ],
            },
        },
        "limits": {
            "vehicles": 10,
            "documents": 200,
            "maintenances": 50,
            "diagnostics": 30,
            "storage_mb": 1024,
        },
    },
    "premium": {
        "_id": "premium",
        "type": "premium",
        "name": "Premium",
        "description": "Pour les professionnels et les flottes.",
        "monthlyPrice": 19.99,
        "yearlyPrice": 199.0,
        "currency": "EUR",
        "yearlyDiscount": 17,
        "isPopular": False,
        "badge": "Pro",
        "colorAccent": "#0F766E",
        "highlights": [
            "Véhicules illimités",
            "Stockage 10 Go",
            "Diagnostics illimités",
        ],
        "features": [
            "Tout le plan Standard",
            "Limites étendues",
            "Support prioritaire 24/7",
        ],
        "featuresByCategory": {
            "Gestion": {
                "name": "Gestion",
                "features": [
                    {
                        "key": "vehicles",
                        "label": "Véhicules",
                        "type": "limit",
                        "value": -1,
                        "displayValue": "Illimité",
                    },
                    {
                        "key": "documents",
                        "label": "Documents",
                        "type": "limit",
                        "value": 1000,
                        "displayValue": "1000 documents",
                    },
                ],
            },
            "Suivi": {
                "name": "Suivi",
                "features": [
                    {
                        "key": "maintenances",
                        "label": "Maintenances/mois",
                        "type": "limit",
                        "value": 200,
                        "displayValue": "200 / mois",
                    },
                    {
                        "key": "diagnostics",
                        "label": "Diagnostics/mois",
                        "type": "limit",
                        "value": -1,
                        "displayValue": "Illimité",
                    },
                ],
            },
            "Stockage": {
                "name": "Stockage",
                "features": [
                    {
                        "key": "storage",
                        "label": "Stockage",
                        "type": "limit",
                        "value": 10240,
                        "displayValue": "10 Go",
                    }
                ],
            },
        },
        "limits": {
            "vehicles": -1,
            "documents": 1000,
            "maintenances": 200,
            "diagnostics": -1,
            "storage_mb": 10240,
        },
    },
}

PLAN_HIERARCHY = {
    "free": 0,
    "standard": 1,
    "premium": 2,
}


def list_plans() -> List[dict]:
    return list(PLAN_CATALOG.values())


def get_plan(plan_code: str) -> dict | None:
    if not plan_code:
        return None
    return PLAN_CATALOG.get(plan_code)


def get_plan_by_id(plan_id: str) -> dict | None:
    return get_plan(plan_id)
