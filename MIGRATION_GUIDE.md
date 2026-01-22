# Guide de Conversion NestJS → Django REST Framework

Ce document explique comment les concepts NestJS ont été convertis en Django REST Framework.

## 📚 Équivalences des Concepts

### Structure de Base

| NestJS | Django | Fichier |
|--------|--------|---------|
| `@Module()` | `apps.py` + `AppConfig` | `apps.py` |
| `@Controller()` | `views.py` (APIView, ViewSet) | `views.py` |
| `@Service()` | Fonctions/Classes dans `services.py` | `services.py` |
| DTO (Data Transfer Object) | `Serializer` | `serializers.py` |
| `@Schema()` (Mongoose) | `Model` | `models.py` |
| Guards | Permissions | `permissions.py` |
| Interceptors | Middleware | `middleware.py` |
| Pipes | Validators | `validators.py` |
| Filters | Exception Handlers | `exceptions.py` |

### Décorateurs & Annotations

| NestJS | Django REST Framework |
|--------|----------------------|
| `@Get()` | `@api_view(['GET'])` ou `def get()` dans ViewSet |
| `@Post()` | `@api_view(['POST'])` ou `def post()` |
| `@Put()` / `@Patch()` | `def put()` / `def patch()` |
| `@Delete()` | `def delete()` |
| `@Body()` | `request.data` |
| `@Param()` | `kwargs['id']` ou `self.kwargs` |
| `@Query()` | `request.query_params` |
| `@Req()` | `request` |
| `@Res()` | `Response` object |
| `@UseGuards()` | `permission_classes = [...]` |
| `@UseInterceptors()` | Middleware ou custom logic |
| `@Injectable()` | Pas d'équivalent (pas de DI par défaut) |

### Authentification & Sécurité

| NestJS | Django |
|--------|--------|
| `JwtStrategy` | `JWTAuthentication` (simplejwt) |
| `PassportModule` | `rest_framework.authentication` |
| `AuthGuard('jwt')` | `permission_classes = [IsAuthenticated]` |
| `@UseGuards(RolesGuard)` | Custom permission classes |
| Passport strategies | Authentication backends |

### Base de Données

| Mongoose (NestJS) | Django ORM |
|-------------------|------------|
| `@Schema()` | `class Model(models.Model)` |
| `@Prop()` | Field types (`CharField`, `IntegerField`, etc.) |
| `@Prop({ required: true })` | `field = models.CharField(..., null=False)` |
| `@Prop({ default: value })` | `field = models.CharField(default=value)` |
| `@Prop({ unique: true })` | `field = models.CharField(unique=True)` |
| `Schema.Types.ObjectId` | `models.ForeignKey()` |
| `ref: 'Model'` | `ForeignKey(Model, ...)` |
| `timestamps: true` | `created_at = models.DateTimeField(auto_now_add=True)` |
| `.find()` | `.filter()` |
| `.findOne()` | `.get()` |
| `.findById()` | `.get(id=...)` |
| `.create()` | `.objects.create()` |
| `.save()` | `.save()` |
| `.update()` | `.update()` |
| `.remove()` | `.delete()` |

### Validation

| NestJS | Django |
|--------|--------|
| `class-validator` (`@IsEmail()`, etc.) | Serializer validators |
| `ValidationPipe` | Serializer `is_valid()` |
| DTO validation | Serializer fields + validators |
| Custom validators | `def validate_field()` in serializer |

### Dependency Injection

NestJS utilise massivement la DI, Django non. Voici les équivalents :

```typescript
// NestJS
constructor(
  private readonly userService: UserService,
  private readonly mailService: MailService
) {}
```

```python
# Django - Import direct
from .services import UserService, MailService

class MyView(APIView):
    def post(self, request):
        user_service = UserService()
        mail_service = MailService()
```

### Configuration

| NestJS | Django |
|--------|--------|
| `ConfigModule` + `.env` | `python-decouple` + `.env` |
| `@ConfigService.get()` | `config('KEY')` |
| Environment variables | `settings.py` avec `config()` |

### Tâches Asynchrones

| NestJS | Django |
|--------|--------|
| `@nestjs/bull` (Redis Queue) | Celery |
| `@Process()` decorator | `@shared_task` ou `@app.task` |
| Queue jobs | Celery tasks |
| Job scheduler | Celery Beat |

### WebSockets

| NestJS | Django |
|--------|--------|
| `@WebSocketGateway()` | Django Channels |
| `@SubscribeMessage()` | Consumer methods |
| `socket.io` | Channels with Redis |

### Tests

| NestJS | Django |
|--------|--------|
| Jest | pytest ou Django TestCase |
| `describe()` / `it()` | `class TestCase` / `def test_` |
| `TestingModule` | Django test client |
| Supertest | Django REST Framework test client |

## 🔄 Exemples de Conversion

### Exemple 1: Controller → View

**NestJS:**
```typescript
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.usersService.findOne(id);
  }

  @Post()
  async create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }
}
```

**Django:**
```python
from rest_framework import viewsets
from rest_framework.decorators import action

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def retrieve(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)
```

### Exemple 2: DTO → Serializer

**NestJS:**
```typescript
export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(6)
  password: string;

  @IsString()
  firstName: string;
}
```

**Django:**
```python
from rest_framework import serializers

class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    first_name = serializers.CharField()
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
```

### Exemple 3: Schema → Model

**NestJS (Mongoose):**
```typescript
@Schema({ timestamps: true })
export class User {
  @Prop({ required: true, unique: true })
  email: string;

  @Prop({ required: true })
  password: string;

  @Prop({ type: [String], default: ['user'] })
  roles: string[];
}
```

**Django:**
```python
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    roles = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Exemple 4: Service

**NestJS:**
```typescript
@Injectable()
export class UsersService {
  constructor(
    @InjectModel(User.name) private userModel: Model<User>
  ) {}

  async findOne(id: string): Promise<User> {
    return this.userModel.findById(id).exec();
  }
}
```

**Django:**
```python
# services.py
from .models import User

class UserService:
    @staticmethod
    def find_one(user_id):
        return User.objects.get(id=user_id)

# Ou simplement dans la view:
user = User.objects.get(id=user_id)
```

## ⚠️ Points d'Attention

### 1. Pas de Dependency Injection Native
Django n'a pas de système DI comme NestJS. Utilisez des imports directs.

### 2. Synchrone par Défaut
Django est synchrone par défaut. Pour l'async, utilisez:
- Django 3.1+ avec ASGI
- Celery pour les tâches longues

### 3. ORM Différent
- Mongoose utilise des promises
- Django ORM est synchrone (sauf avec async views)

### 4. Routing
- NestJS: Décorateurs sur les méthodes
- Django: `urls.py` centralisé

### 5. Middleware
- NestJS: Interceptors, Guards, Pipes
- Django: Middleware + Permissions

## 📝 Checklist de Migration

- [ ] Convertir les schemas en models
- [ ] Créer les serializers depuis les DTOs
- [ ] Convertir les controllers en views/viewsets
- [ ] Extraire la logique des services
- [ ] Configurer les URLs
- [ ] Mettre en place l'authentification JWT
- [ ] Configurer les permissions
- [ ] Migrer les tâches background vers Celery
- [ ] Adapter les tests
- [ ] Configurer les variables d'environnement
- [ ] Documenter l'API (Swagger/OpenAPI)

## 🚀 Avantages de Django

1. **Admin automatique** - Interface d'administration prête à l'emploi
2. **ORM puissant** - Migrations automatiques, queries optimisées
3. **Écosystème mature** - Nombreux packages disponibles
4. **Documentation excellente** - Très complète et à jour
5. **Sécurité intégrée** - CSRF, XSS, SQL injection protection
6. **Scalabilité** - Utilisé par Instagram, Pinterest, etc.

## 📚 Ressources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Celery Documentation](https://docs.celeryproject.org/)
