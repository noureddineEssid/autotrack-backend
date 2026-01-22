#!/bin/bash

# Script pour démarrer le backend Django AutoTrack
# Usage: ./start-backend.sh

echo "=========================================="
echo "Démarrage du Backend AutoTrack"
echo "=========================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Chemin du projet
BACKEND_DIR="/home/nessid/projects/autotrack-backend"

# Vérifier si le dossier existe
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Dossier backend non trouvé: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR" || exit

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Environnement virtuel non trouvé. Création...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
fi

# Activer l'environnement virtuel
echo -e "${YELLOW}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Vérifier si Django est installé
if ! python -c "import django" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Django non installé. Installation des dépendances...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dépendances installées${NC}"
fi

# Appliquer les migrations
echo -e "${YELLOW}Application des migrations...${NC}"
python manage.py migrate

# Afficher l'IP locale
echo ""
echo "=========================================="
echo "Configuration Réseau"
echo "=========================================="
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo -e "IP Locale: ${GREEN}$LOCAL_IP${NC}"
echo ""
echo "URLs d'accès:"
echo -e "  • Localhost:     ${GREEN}http://localhost:8000${NC}"
echo -e "  • Android Emu:   ${GREEN}http://10.0.2.2:8000${NC}"
echo -e "  • iOS Simulator: ${GREEN}http://localhost:8000${NC}"
echo -e "  • Appareil Réel: ${GREEN}http://$LOCAL_IP:8000${NC}"
echo "=========================================="
echo ""

# Démarrer le serveur
echo -e "${GREEN}🚀 Démarrage du serveur Django...${NC}"
echo -e "${YELLOW}Appuyez sur CTRL+C pour arrêter${NC}"
echo ""

python manage.py runserver 0.0.0.0:8000
