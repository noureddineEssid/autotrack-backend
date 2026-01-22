"""
Script de migration de données depuis MongoDB (NestJS) vers PostgreSQL/SQLite (Django)

Ce script peut être utilisé pour migrer les données existantes du projet NestJS
vers le nouveau projet Django.

ATTENTION: Assurez-vous que les deux bases de données sont accessibles avant d'exécuter ce script.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autotrack_backend.settings')
django.setup()

from users.models import User
from vehicles.models import Vehicle, CarBrand, CarModel
from maintenances.models import Maintenance
from garages.models import Garage
# Ajouter d'autres imports selon les besoins

def migrate_users():
    """
    Migrer les utilisateurs depuis MongoDB vers Django
    
    TODO: Implémenter la connexion à MongoDB et la migration
    """
    print("Migration des utilisateurs...")
    # Connexion à MongoDB
    # Récupération des users
    # Création dans Django
    pass

def migrate_vehicles():
    """Migrer les véhicules"""
    print("Migration des véhicules...")
    pass

def migrate_maintenances():
    """Migrer les maintenances"""
    print("Migration des maintenances...")
    pass

def migrate_all():
    """Exécuter toutes les migrations"""
    print("Début de la migration des données...")
    print("-" * 50)
    
    # Ordre important : d'abord les users, puis les objets qui dépendent d'eux
    migrate_users()
    migrate_vehicles()
    migrate_maintenances()
    
    print("-" * 50)
    print("Migration terminée!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrer les données de MongoDB vers Django')
    parser.add_argument('--users', action='store_true', help='Migrer uniquement les utilisateurs')
    parser.add_argument('--vehicles', action='store_true', help='Migrer uniquement les véhicules')
    parser.add_argument('--all', action='store_true', help='Migrer toutes les données')
    
    args = parser.parse_args()
    
    if args.users:
        migrate_users()
    elif args.vehicles:
        migrate_vehicles()
    elif args.all:
        migrate_all()
    else:
        print("Utilisez --help pour voir les options disponibles")
        print("Exemple: python scripts/migrate_data.py --all")
