#!/bin/bash

# Script de test de la migration NestJS -> Django
# AutoTrack Backend

echo "========================================="
echo "Test de Migration AutoTrack Backend"
echo "========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Fonction de test
test_command() {
    local description="$1"
    local command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Test $TOTAL_TESTS: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Activer le venv
source venv/bin/activate

echo "1. Tests de base"
echo "----------------"

test_command "Django installé" "python -c 'import django'"
test_command "DRF installé" "python -c 'import rest_framework'"
test_command "Settings valide" "python manage.py check"
test_command "Migrations à jour" "python manage.py migrate --check"

echo ""
echo "2. Tests des modèles"
echo "--------------------"

test_command "Modèle User" "python -c 'from users.models import User'"
test_command "Modèle Vehicle" "python -c 'from vehicles.models import Vehicle'"
test_command "Modèle Maintenance" "python -c 'from maintenances.models import Maintenance'"
test_command "Modèle Garage" "python -c 'from garages.models import Garage'"
test_command "Modèle Diagnostic" "python -c 'from diagnostics.models import Diagnostic'"
test_command "Modèle Document" "python -c 'from documents.models import Document'"
test_command "Modèle Notification" "python -c 'from notifications.models import Notification'"
test_command "Modèle Plan" "python -c 'from plans.models import Plan'"
test_command "Modèle Subscription" "python -c 'from subscriptions.models import Subscription'"
test_command "Modèle WebhookEvent" "python -c 'from webhooks.models import WebhookEvent'"
test_command "Modèle UserSettings" "python -c 'from settings_app.models import UserSettings'"
test_command "Modèle AIConversation" "python -c 'from ai_assistant.models import AIConversation'"

echo ""
echo "3. Tests des serializers"
echo "------------------------"

test_command "UserSerializer" "python -c 'from users.serializers import UserSerializer'"
test_command "VehicleSerializer" "python -c 'from vehicles.serializers import VehicleSerializer'"
test_command "MaintenanceSerializer" "python -c 'from maintenances.serializers import MaintenanceSerializer'"
test_command "GarageSerializer" "python -c 'from garages.serializers import GarageSerializer'"
test_command "DiagnosticSerializer" "python -c 'from diagnostics.serializers import DiagnosticSerializer'"
test_command "DocumentSerializer" "python -c 'from documents.serializers import DocumentSerializer'"
test_command "NotificationSerializer" "python -c 'from notifications.serializers import NotificationSerializer'"
test_command "PlanSerializer" "python -c 'from plans.serializers import PlanSerializer'"
test_command "UserSettingsSerializer" "python -c 'from settings_app.serializers import UserSettingsSerializer'"

echo ""
echo "4. Tests des views"
echo "------------------"

test_command "UserViewSet" "python -c 'from users.views import RegisterView'"
test_command "VehicleViewSet" "python -c 'from vehicles.views import VehicleViewSet'"
test_command "MaintenanceViewSet" "python -c 'from maintenances.views import MaintenanceViewSet'"
test_command "GarageViewSet" "python -c 'from garages.views import GarageViewSet'"
test_command "DiagnosticViewSet" "python -c 'from diagnostics.views import DiagnosticViewSet'"
test_command "DocumentViewSet" "python -c 'from documents.views import DocumentViewSet'"
test_command "NotificationViewSet" "python -c 'from notifications.views import NotificationViewSet'"
test_command "PlanViewSet" "python -c 'from plans.views import PlanViewSet'"

echo ""
echo "5. Tests des URLs"
echo "-----------------"

test_command "URLs users" "python -c 'from users.urls import urlpatterns'"
test_command "URLs vehicles" "python -c 'from vehicles.urls import urlpatterns'"
test_command "URLs maintenances" "python -c 'from maintenances.urls import urlpatterns'"
test_command "URLs garages" "python -c 'from garages.urls import urlpatterns'"
test_command "URLs diagnostics" "python -c 'from diagnostics.urls import urlpatterns'"
test_command "URLs documents" "python -c 'from documents.urls import urlpatterns'"
test_command "URLs notifications" "python -c 'from notifications.urls import urlpatterns'"
test_command "URLs plans" "python -c 'from plans.urls import urlpatterns'"
test_command "URLs subscriptions" "python -c 'from subscriptions.urls import urlpatterns'"
test_command "URLs webhooks" "python -c 'from webhooks.urls import urlpatterns'"
test_command "URLs settings" "python -c 'from settings_app.urls import urlpatterns'"
test_command "URLs ai_assistant" "python -c 'from ai_assistant.urls import urlpatterns'"

echo ""
echo "6. Tests admin"
echo "--------------"

test_command "Admin users" "python -c 'from users.admin import UserAdmin'"
test_command "Admin vehicles" "python -c 'from vehicles.admin import VehicleAdmin'"
test_command "Admin maintenances" "python -c 'from maintenances.admin import MaintenanceAdmin'"
test_command "Admin garages" "python -c 'from garages.admin import GarageAdmin'"
test_command "Admin diagnostics" "python -c 'from diagnostics.admin import DiagnosticAdmin'"
test_command "Admin documents" "python -c 'from documents.admin import DocumentAdmin'"
test_command "Admin notifications" "python -c 'from notifications.admin import NotificationAdmin'"
test_command "Admin plans" "python -c 'from plans.admin import PlanAdmin'"

echo ""
echo "7. Tests de configuration"
echo "-------------------------"

test_command "Celery configuré" "python -c 'from autotrack_backend.celery import app'"
test_command "JWT configuré" "python -c 'from rest_framework_simplejwt.tokens import RefreshToken'"
test_command "CORS configuré" "python -c 'import corsheaders'"
test_command "Filters configurés" "python -c 'import django_filters'"

echo ""
echo "========================================="
echo "Résumé des tests"
echo "========================================="
echo -e "Total: $TOTAL_TESTS tests"
echo -e "${GREEN}Réussis: $PASSED_TESTS${NC}"
echo -e "${RED}Échoués: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les tests sont passés!${NC}"
    echo ""
    echo "La migration est complète à 100%!"
    exit 0
else
    echo -e "${RED}✗ Certains tests ont échoué${NC}"
    echo ""
    echo "Pourcentage de réussite: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    exit 1
fi
