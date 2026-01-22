# Guide de Test de l'API Autotrack

Ce fichier contient des exemples de requêtes pour tester l'API.

## Configuration

### Démarrer le serveur
```bash
cd /home/nessid/projects/autotrack-backend
source venv/bin/activate
python manage.py runserver
```

Le serveur sera disponible sur: http://localhost:8000

## Tests des Endpoints d'Authentification

### 1. Inscription (Register)

**Requête:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+33612345678"
  }'
```

**Réponse attendue (201 Created):**
```json
{
  "user": {
    "id": 2,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+33612345678",
    "roles": ["user"],
    "email_verified": false,
    "created_at": "2026-01-21T10:00:00Z",
    "updated_at": "2026-01-21T10:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 2. Connexion (Login)

**Requête:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
  }'
```

**Réponse attendue (200 OK):**
```json
{
  "user": {
    "id": 2,
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    ...
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

**⚠️ Sauvegardez le token d'accès pour les requêtes suivantes !**

### 3. Récupérer le Profil (Me)

**Requête:**
```bash
# Remplacez YOUR_ACCESS_TOKEN par le token reçu lors du login
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse attendue (200 OK):**
```json
{
  "id": 2,
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+33612345678",
  "roles": ["user"],
  "email_verified": false,
  "created_at": "2026-01-21T10:00:00Z",
  "updated_at": "2026-01-21T10:00:00Z"
}
```

### 4. Mettre à jour le Profil

**Requête:**
```bash
curl -X PUT http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone_number": "+33698765432"
  }'
```

### 5. Changer le Mot de Passe

**Requête:**
```bash
curl -X POST http://localhost:8000/api/auth/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password_confirm": "NewSecurePass456!"
  }'
```

**Réponse attendue (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

### 6. Lister les Sessions Actives

**Requête:**
```bash
curl -X GET http://localhost:8000/api/auth/sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse attendue:**
```json
[
  {
    "id": 1,
    "ip_address": "127.0.0.1",
    "user_agent": "curl/7.68.0",
    "is_active": true,
    "expires_at": "2026-02-20T10:00:00Z",
    "created_at": "2026-01-21T10:00:00Z"
  }
]
```

### 7. Rafraîchir le Token

**Requête:**
```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Réponse attendue:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 8. Déconnexion (Logout)

**Requête:**
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse attendue (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

## Tests avec Python

### Installation de requests
```bash
pip install requests
```

### Script de test
```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(f"{BASE_URL}/api/auth/register/", json={
    "email": "test@example.com",
    "password": "Test123!",
    "password_confirm": "Test123!",
    "first_name": "Test",
    "last_name": "User"
})
print("Register:", response.status_code)
data = response.json()
print(data)

# 2. Login
response = requests.post(f"{BASE_URL}/api/auth/login/", json={
    "email": "test@example.com",
    "password": "Test123!"
})
print("\nLogin:", response.status_code)
data = response.json()
access_token = data['tokens']['access']
print("Access Token:", access_token[:50] + "...")

# 3. Get Profile
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/auth/me/", headers=headers)
print("\nProfile:", response.status_code)
print(response.json())

# 4. Update Profile
response = requests.put(
    f"{BASE_URL}/api/auth/me/",
    headers=headers,
    json={"first_name": "Updated", "last_name": "Name"}
)
print("\nUpdate:", response.status_code)

# 5. Get Sessions
response = requests.get(f"{BASE_URL}/api/auth/sessions/", headers=headers)
print("\nSessions:", response.status_code)
print(response.json())

# 6. Logout
response = requests.post(f"{BASE_URL}/api/auth/logout/", headers=headers)
print("\nLogout:", response.status_code)
print(response.json())
```

## Tests avec Postman

### Collection Postman

Importez cette configuration dans Postman:

```json
{
  "info": {
    "name": "Autotrack API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Register",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"Test123!\",\n  \"password_confirm\": \"Test123!\",\n  \"first_name\": \"Test\",\n  \"last_name\": \"User\"\n}"
            },
            "url": "http://localhost:8000/api/auth/register/"
          }
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"Test123!\"\n}"
            },
            "url": "http://localhost:8000/api/auth/login/"
          }
        },
        {
          "name": "Me",
          "request": {
            "method": "GET",
            "header": [{"key": "Authorization", "value": "Bearer {{access_token}}"}],
            "url": "http://localhost:8000/api/auth/me/"
          }
        }
      ]
    }
  ]
}
```

## Codes de Statut HTTP

- **200 OK** - Requête réussie
- **201 Created** - Ressource créée avec succès
- **400 Bad Request** - Données invalides
- **401 Unauthorized** - Non authentifié
- **403 Forbidden** - Accès refusé
- **404 Not Found** - Ressource non trouvée
- **500 Internal Server Error** - Erreur serveur

## Messages d'Erreur Courants

### Email déjà existant
```json
{
  "email": ["user with this email already exists."]
}
```

### Mots de passe ne correspondent pas
```json
{
  "password": ["Passwords don't match"]
}
```

### Token invalide
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid"
}
```

### Identifiants invalides
```json
{
  "non_field_errors": ["Invalid email or password"]
}
```

## Accès à l'Admin Django

URL: http://localhost:8000/admin/

**Compte admin créé:**
- Email: admin@autotrack.com
- Password: admin123

**Compte test (à créer):**
- Email: test@autotrack.com
- Password: test123

## Prochaines Étapes

Une fois les tests d'authentification validés, vous pourrez tester:
- CRUD Vehicles
- CRUD Maintenances
- CRUD Garages
- etc.

Ces endpoints seront créés dans la prochaine phase de développement.
