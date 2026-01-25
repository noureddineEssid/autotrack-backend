from django.core.management.base import BaseCommand
from ai_assistant.models import AIConversation, AIMessage
from users.models import User
import random


class Command(BaseCommand):
    help = 'Seeds the AI assistant tables with test data'

    def handle(self, *args, **kwargs):
        # Nettoyer les conversations existantes
        AIConversation.objects.all().delete()
        self.stdout.write('AI Assistant tables cleared')
        
        users = list(User.objects.all())
        
        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return
        
        # Créer les conversations
        self.stdout.write('\nCreating AI conversations...')
        created_conversations = []
        
        conversation_topics = [
            'Questions sur l\'entretien de mon véhicule',
            'Problème de bruit moteur',
            'Recommandations pour la vidange',
            'Conseils pour économiser du carburant',
            'Préparation au contrôle technique',
            'Diagnostic de voyant moteur',
            'Choix de pneus pour l\'hiver',
            'Questions sur l\'assurance automobile',
        ]
        
        for i in range(15):  # Créer 15 conversations
            user = random.choice(users)
            topic = random.choice(conversation_topics)
            
            conversation = AIConversation.objects.create(
                user=user,
                title=topic,
                is_active=random.random() > 0.3  # 70% actives
            )
            created_conversations.append(conversation)
        
        self.stdout.write(f'  ✓ Created {len(created_conversations)} conversations')
        
        # Créer les messages pour chaque conversation
        self.stdout.write('\nCreating AI messages...')
        messages_created = 0
        
        sample_exchanges = [
            {
                'user': 'Bonjour, je voudrais savoir quand faire la prochaine vidange de ma voiture ?',
                'assistant': 'Bonjour ! Pour vous donner une recommandation précise, je consulte les données de votre véhicule. En général, une vidange est recommandée tous les 10 000 à 15 000 km ou une fois par an. Pouvez-vous me dire combien de kilomètres a parcouru votre véhicule depuis la dernière vidange ?'
            },
            {
                'user': 'Ma voiture fait un bruit bizarre au démarrage, qu\'est-ce que ça peut être ?',
                'assistant': 'Un bruit au démarrage peut avoir plusieurs origines. Pouvez-vous me décrire plus précisément le type de bruit (sifflement, grincement, claquement) ? Et à quel moment exactement se produit-il : au moment de tourner la clé ou juste après le démarrage du moteur ?'
            },
            {
                'user': 'Comment puis-je économiser du carburant ?',
                'assistant': 'Voici quelques conseils pour réduire votre consommation de carburant : 1) Adoptez une conduite souple en anticipant les freinages, 2) Vérifiez régulièrement la pression de vos pneus, 3) Évitez les charges inutiles dans le coffre, 4) Utilisez la climatisation avec modération, 5) Entretenez régulièrement votre véhicule.'
            },
        ]
        
        for conversation in created_conversations:
            # Nombre de messages aléatoire entre 2 et 10
            num_exchanges = random.randint(1, 3)
            
            for j in range(num_exchanges):
                exchange = random.choice(sample_exchanges)
                
                # Message utilisateur
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=exchange['user'],
                    metadata={'timestamp': 'user_message'}
                )
                messages_created += 1
                
                # Réponse assistant
                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=exchange['assistant'],
                    metadata={'timestamp': 'assistant_response'}
                )
                messages_created += 1
        
        self.stdout.write(f'  ✓ Created {messages_created} messages')
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created AI assistant data:'))
        self.stdout.write(f'   • {len(created_conversations)} conversations')
        self.stdout.write(f'   • {messages_created} messages')
