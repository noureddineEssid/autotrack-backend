# Quick Start Guide - Autotrack Backend Django

## Démarrage Rapide

### 1. Installer les dépendances (déjà fait)
```bash
cd /home/nessid/projects/autotrack-backend
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Appliquer les migrations (déjà fait)
```bash
python manage.py migrate
```

### 3. Créer un superutilisateur (déjà créé)
- Email: admin@autotrack.com
- Password: admin123

Ou créer manuellement:
```bash
python manage.py createsuperuser
```

### 4. Démarrer le serveur
```bash
python manage.py runserver
```

### 5. Accéder à l'application
- API: http://localhost:8000/
- Admin: http://localhost:8000/admin/
- API Auth: http://localhost:8000/api/auth/

## Test de l'API

### 1. Register (Inscription)
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. Login (Connexion)
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

Réponse:
```json
{
  "user": {
    "id": 1,
    "email": "test@example.com",
    "first_name": "John",
    "last_name": "Doe",
    ...
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJh...",
    "access": "eyJ0eXAiOiJKV1QiLCJh..."
  }
}
```

### 3. Get Current User (Me)
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Refresh Token
```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## Structure des Réponses

### Success Response
```json
{
  "user": {...},
  "tokens": {
    "access": "...",
    "refresh": "..."
  }
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

## Prochaines Étapes

1. Implémenter les endpoints pour vehicles
2. Implémenter les endpoints pour maintenances
3. Implémenter les endpoints pour garages
4. Ajouter les services (Email, AI, Stripe)
5. Configurer les webhooks Stripe
6. Ajouter les tests

## Variables d'Environnement Importantes

Éditer `.env` pour configurer:
- SECRET_KEY
- DEBUG
- DATABASE (PostgreSQL pour production)
- STRIPE_SECRET_KEY
- OPENAI_API_KEY
- EMAIL_HOST_USER et EMAIL_HOST_PASSWORD
- REDIS_URL (pour Celery)
