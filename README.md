# Autotrack Backend - Django REST API

Ce projet est la version Django REST API du backend Autotrack, converti depuis NestJS.

## 🚀 Stack Technique

- **Framework**: Django 5.2.10
- **API**: Django REST Framework 3.16.1
- **Authentification**: JWT (djangorestframework-simplejwt)
- **Base de données**: PostgreSQL (avec support SQLite pour développement)
- **Cache/Queue**: Redis
- **Tâches asynchrones**: Celery
- **Paiements**: Stripe
- **IA**: OpenAI API
- **OCR**: Tesseract

## 📦 Installation

### Prérequis

- Python 3.12+
- PostgreSQL 15+ (ou SQLite pour développement)
- Redis 7+

### Configuration

1. **Cloner le projet et créer l'environnement virtuel**

```bash
cd /home/nessid/projects/autotrack-backend
python3 -m venv venv
source venv/bin/activate
```

2. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

3. **Configuration des variables d'environnement**

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

4. **Créer la base de données**

```bash
# PostgreSQL
createdb autotrack_db

# Ou utiliser SQLite (par défaut pour développement)
```

5. **Appliquer les migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un superutilisateur**

```bash
python manage.py createsuperuser
```

## 🏃 Démarrage

### Mode développement

```bash
# Terminal 1 - Django server
python manage.py runserver

# Terminal 2 - Celery worker (optionnel)
celery -A autotrack_backend worker -l info

# Terminal 3 - Celery beat (pour les tâches planifiées)
celery -A autotrack_backend beat -l info
```

### Mode production

```bash
# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Utiliser Gunicorn
gunicorn autotrack_backend.wsgi:application --bind 0.0.0.0:8000
```

## 📊 Structure du Projet

```
autotrack-backend/
├── autotrack_backend/          # Configuration principale Django
│   ├── settings.py            # Paramètres Django
│   ├── urls.py                # URLs principales
│   ├── celery.py              # Configuration Celery
│   └── wsgi.py                # WSGI application
├── users/                      # Application utilisateurs
│   ├── models.py              # User, Session
│   ├── serializers.py         # Serializers DRF
│   ├── views.py               # Views API
│   └── urls.py                # Routes
├── vehicles/                   # Application véhicules
│   ├── models.py              # Vehicle, CarBrand, CarModel
│   └── ...
├── maintenances/              # Application maintenances
├── garages/                   # Application garages
├── diagnostics/               # Application diagnostics
├── subscriptions/             # Application abonnements
├── plans/                     # Application plans tarifaires
├── documents/                 # Application documents
├── notifications/             # Application notifications
├── webhooks/                  # Webhooks Stripe
├── settings_app/              # Paramètres utilisateur
├── ai_assistant/              # Assistant IA
├── manage.py                  # CLI Django
└── requirements.txt           # Dépendances Python
```

## 🔑 Modèles de Données

### Users
- **User**: Utilisateur avec authentification JWT, OTP, Stripe
- **Session**: Sessions utilisateur

### Vehicles
- **Vehicle**: Véhicule d'un utilisateur
- **CarBrand**: Marque de voiture
- **CarModel**: Modèle de voiture

### Maintenances
- **Maintenance**: Entretien de véhicule

### Garages
- **Garage**: Garage avec géolocalisation
- **GarageReview**: Avis sur les garages

### Plans & Subscriptions
- **Plan**: Plan d'abonnement
- **PlanFeature**: Fonctionnalités des plans
- **PlanFeatureValue**: Valeurs des fonctionnalités
- **Subscription**: Abonnement utilisateur
- **SubscriptionHistory**: Historique des changements

### Documents
- **Document**: Documents avec OCR

### Diagnostics
- **Diagnostic**: Diagnostic véhicule
- **DiagnosticReply**: Conversations diagnostic

### Notifications
- **Notification**: Notifications utilisateur

### AI Assistant
- **AIConversation**: Conversation avec IA
- **AIMessage**: Messages de conversation

### Webhooks
- **StripeEvent**: Événements webhook Stripe

## 🔌 API Endpoints

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `POST /api/auth/logout/` - Déconnexion
- `GET /api/auth/me/` - Profil utilisateur
- `PUT /api/auth/me/` - Mise à jour profil
- `POST /api/auth/change-password/` - Changer mot de passe
- `GET /api/auth/sessions/` - Liste des sessions
- `POST /api/token/refresh/` - Rafraîchir token JWT

### Autres endpoints
(À développer dans les prochaines étapes)

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Tests avec coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔒 Sécurité

- Authentification JWT avec refresh tokens
- CORS configuré
- CSRF protection
- Password hashing avec bcrypt
- Rate limiting (à configurer)
- Validation des uploads de fichiers

## 📝 Tâches Celery

Les tâches suivantes peuvent être implémentées :
- Envoi d'emails
- Rappels de maintenance
- Traitement OCR de documents
- Synchronisation Stripe
- Nettoyage des sessions expirées

## 🔄 Migration depuis NestJS

Ce projet a été converti depuis le projet NestJS `autotrack-backend-old`. Les principales équivalences :

| NestJS | Django |
|--------|--------|
| @Module | apps.py |
| @Controller | views.py |
| @Service | services.py (à créer) |
| @Injectable | Pas d'équivalent direct |
| DTO | serializers.py |
| @Schema (Mongoose) | models.py |
| Guards | permissions.py |
| Interceptors | middleware.py |
| Pipes | validators |

## 🚧 TODO

- [ ] Créer les views pour tous les modules
- [ ] Implémenter les services (email, AI, Stripe)
- [ ] Ajouter les tests unitaires
- [ ] Configurer les tâches Celery
- [ ] Ajouter la documentation Swagger/OpenAPI
- [ ] Configurer Docker
- [ ] Ajouter les webhooks Stripe
- [ ] Implémenter les permissions personnalisées

## 📄 License

Privé
