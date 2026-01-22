#!/bin/bash

# Script de commandes utiles pour Autotrack Backend

echo "=== Autotrack Backend - Commandes Utiles ==="
echo ""

# Fonction pour afficher le menu
show_menu() {
    echo "Choisissez une action:"
    echo "1. Démarrer le serveur de développement"
    echo "2. Créer un superutilisateur"
    echo "3. Créer les migrations"
    echo "4. Appliquer les migrations"
    echo "5. Démarrer Celery worker"
    echo "6. Démarrer Celery beat"
    echo "7. Shell Django interactif"
    echo "8. Collecter les fichiers statiques"
    echo "9. Lancer les tests"
    echo "10. Démarrer avec Docker Compose"
    echo "11. Créer un utilisateur de test"
    echo "12. Afficher les URL disponibles"
    echo "0. Quitter"
    echo ""
}

# Activer l'environnement virtuel
activate_venv() {
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ Environnement virtuel non trouvé. Créez-le avec: python3 -m venv venv"
        exit 1
    fi
}

# Naviguer vers le répertoire du projet
cd /home/nessid/projects/autotrack-backend

while true; do
    show_menu
    read -p "Votre choix: " choice
    
    case $choice in
        1)
            echo "🚀 Démarrage du serveur..."
            activate_venv
            python manage.py runserver
            ;;
        2)
            echo "👤 Création d'un superutilisateur..."
            activate_venv
            python manage.py createsuperuser
            ;;
        3)
            echo "📝 Création des migrations..."
            activate_venv
            python manage.py makemigrations
            ;;
        4)
            echo "⚡ Application des migrations..."
            activate_venv
            python manage.py migrate
            ;;
        5)
            echo "🔄 Démarrage de Celery worker..."
            activate_venv
            celery -A autotrack_backend worker -l info
            ;;
        6)
            echo "⏰ Démarrage de Celery beat..."
            activate_venv
            celery -A autotrack_backend beat -l info
            ;;
        7)
            echo "🐚 Shell Django..."
            activate_venv
            python manage.py shell
            ;;
        8)
            echo "📦 Collecte des fichiers statiques..."
            activate_venv
            python manage.py collectstatic --noinput
            ;;
        9)
            echo "🧪 Lancement des tests..."
            activate_venv
            python manage.py test
            ;;
        10)
            echo "🐳 Démarrage avec Docker Compose..."
            docker-compose up
            ;;
        11)
            echo "👥 Création d'un utilisateur de test..."
            activate_venv
            python manage.py shell -c "
from users.models import User
try:
    user = User.objects.create_user(
        email='test@autotrack.com',
        password='test123',
        first_name='Test',
        last_name='User'
    )
    print('✅ Utilisateur créé: test@autotrack.com / test123')
except Exception as e:
    print(f'❌ Erreur: {e}')
"
            ;;
        12)
            echo "📋 URLs disponibles:"
            activate_venv
            python manage.py show_urls 2>/dev/null || echo "
API Endpoints:
- POST   /api/auth/register/
- POST   /api/auth/login/
- POST   /api/auth/logout/
- GET    /api/auth/me/
- PUT    /api/auth/me/
- POST   /api/auth/change-password/
- GET    /api/auth/sessions/
- POST   /api/token/refresh/
- GET    /admin/
"
            ;;
        0)
            echo "👋 Au revoir!"
            exit 0
            ;;
        *)
            echo "❌ Choix invalide. Réessayez."
            ;;
    esac
    
    echo ""
    read -p "Appuyez sur Entrée pour continuer..."
    clear
done
