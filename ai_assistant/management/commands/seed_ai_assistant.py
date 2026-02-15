from django.core.management.base import BaseCommand
from ai_assistant.models import AIConversation, AIMessage
from users.models import User


class Command(BaseCommand):
    help = 'Seeds the AI assistant tables with realistic data'

    def handle(self, *args, **kwargs):
        AIConversation.objects.all().delete()
        self.stdout.write('AI Assistant tables cleared')

        users = list(
            User.objects.filter(
                email__in=[
                    'amal.benali@example.com',
                    'youssef.chaari@example.com',
                    'salma.trabelsi@example.com',
                ]
            )
        )

        if not users:
            self.stdout.write(self.style.WARNING('⚠️  No users found. Please run seed_users first.'))
            return

        self.stdout.write('\nCreating AI conversations...')
        created_conversations = []

        conversation_topics = [
            'Planifier une revision annuelle',
            'Bruit moteur au demarrage',
            'Conseils pour economiser du carburant',
            'Preparation au controle technique',
        ]

        for user in users:
            for i in range(2):
                topic = conversation_topics[(i + 1) % len(conversation_topics)]
                conversation = AIConversation.objects.create(
                    user=user,
                    title=topic,
                    is_active=True,
                )
                created_conversations.append(conversation)

        self.stdout.write(f'  ✓ Created {len(created_conversations)} conversations')

        self.stdout.write('\nCreating AI messages...')
        messages_created = 0

        sample_exchanges = [
            {
                'user': 'Bonjour, quand dois-je faire la prochaine vidange ?',
                'assistant': 'En general, une vidange est recommandee tous les 10 000 a 15 000 km ou une fois par an. Voulez-vous que je consulte votre historique ?',
            },
            {
                'user': 'Ma voiture fait un bruit au demarrage, est-ce grave ?',
                'assistant': 'Un bruit au demarrage peut venir de la batterie, du demarreur ou d\'une courroie. Pouvez-vous decrire le bruit ?'
            },
        ]

        for conversation in created_conversations:
            for exchange in sample_exchanges:
                AIMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=exchange['user'],
                    metadata={'source': 'seed'},
                )
                messages_created += 1

                AIMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=exchange['assistant'],
                    metadata={'source': 'seed'},
                )
                messages_created += 1

        self.stdout.write(f'  ✓ Created {messages_created} messages')
        self.stdout.write(self.style.SUCCESS('\n✅ Successfully created AI assistant data:'))
        self.stdout.write(f'   • {len(created_conversations)} conversations')
        self.stdout.write(f'   • {messages_created} messages')
