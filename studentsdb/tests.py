from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from .models import Student, StudentConversation, ConversationMessage, MessageReadStatus
from channels.testing import WebsocketCommunicator
from core.asgi import application
import asyncio
from django.db.models import Count, Q, F

class ConversationModelTests(TestCase):
    def test_conversation_auto_created_on_student_create(self):
        s = Student.objects.create(first_name='John', last_name='Doe', email='john@example.com', mode_of_class='ON', week_type='WD')
        conv = StudentConversation.objects.filter(student=s).first()
        self.assertIsNotNone(conv)

    def test_message_creation(self):
        s = Student.objects.create(first_name='Jane', last_name='Doe', email='jane@example.com', mode_of_class='ON', week_type='WD')
        conv = StudentConversation.objects.get(student=s)
        User = get_user_model()
        u = User.objects.create_user(email='tester@example.com', name='Tester', role='staff', password=None)
        m = ConversationMessage.objects.create(conversation=conv, sender=u, sender_role='staff', message='Hello')
        self.assertEqual(conv.messages.count(), 1)
        self.assertEqual(m.message, 'Hello')

    def test_unread_mention_count_annotation(self):
        User = get_user_model()
        user = User.objects.create_user(email='viewer@example.com', name='Viewer', role='staff', password='pass')
        student = Student.objects.create(first_name='S', last_name='M', email='s@m.com', mode_of_class='ON', week_type='WD')
        conv, _ = StudentConversation.objects.get_or_create(student=student)
        
        # Message 1: Mention user, unread
        m1 = ConversationMessage.objects.create(conversation=conv, message='@Viewer unread', sender=user)
        m1.mentions.add(user)
        
        # Message 2: Mention user, read
        m2 = ConversationMessage.objects.create(conversation=conv, message='@Viewer read', sender=user)
        m2.mentions.add(user)
        MessageReadStatus.objects.create(message=m2, user=user)
        
        # Message 3: No mention
        m3 = ConversationMessage.objects.create(conversation=conv, message='No mention', sender=user)
        
        # Verify the annotation logic directly matches the view
        qs = Student.objects.filter(pk=student.pk).annotate(
            total_user_mentions=Count(
                'conversation__messages',
                filter=Q(conversation__messages__mentions=user),
                distinct=True
            ),
            read_user_mentions=Count(
                'conversation__messages',
                filter=Q(
                    conversation__messages__mentions=user,
                    conversation__messages__read_statuses__user=user
                ),
                distinct=True
            )
        ).annotate(
            unread_mention_count=F('total_user_mentions') - F('read_user_mentions')
        )
        
        s_annotated = qs.first()
        # Should have 1 unread mention (m1)
        self.assertEqual(s_annotated.unread_mention_count, 1)
        
        # Mark m1 as read
        MessageReadStatus.objects.create(message=m1, user=user)
        
        s_annotated_2 = qs.first()
        self.assertEqual(s_annotated_2.unread_mention_count, 0)

class ConversationWebSocketTests(TransactionTestCase):
    reset_sequences = True

    def test_websocket_broadcast_updates_for_student(self):
        User = get_user_model()
        user = User.objects.create_user(email='tester@example.com', name='Tester', role='staff', password='pass12345')
        student = Student.objects.create(first_name='WS', last_name='User', email='ws@example.com', mode_of_class='ON', week_type='WD')
        client = self.client
        client.login(email='tester@example.com', password='pass12345')
        sessionid = client.cookies.get('sessionid').value

        async def run_flow():
            path = f"/ws/student/{student.pk}/"
            headers = [(b"cookie", f"sessionid={sessionid}".encode())]

            comm1 = WebsocketCommunicator(application, path)
            comm1.scope['headers'] = headers
            connected1, _ = await comm1.connect()
            assert connected1
            init1 = await comm1.receive_json_from()
            assert init1.get('action') == 'init'

            comm2 = WebsocketCommunicator(application, path)
            connected2, _ = await comm2.connect()
            assert connected2
            init2 = await comm2.receive_json_from()
            assert init2.get('action') == 'init'

            await comm1.send_json_to({"action": "send", "message": "Hello WebSocket"})

            msg1 = await comm1.receive_json_from()
            msg2 = await comm2.receive_json_from()
            assert msg1.get('action') == 'new_message'
            assert msg2.get('action') == 'new_message'
            assert msg1['message']['message'] == 'Hello WebSocket'
            assert msg1['message']['sender_role'] == 'staff'

            await comm1.disconnect()
            await comm2.disconnect()

        asyncio.run(run_flow())

        conv = StudentConversation.objects.get(student=student)
        self.assertEqual(conv.messages.count(), 1)

    def test_notification_broadcast(self):
        User = get_user_model()
        sender = User.objects.create_user(email='sender@example.com', name='Sender', role='staff', password='pass12345')
        recipient = User.objects.create_user(email='recipient@example.com', name='Recipient', role='staff', password='pass12345')
        student = Student.objects.create(first_name='Notif', last_name='User', email='notif@example.com', mode_of_class='ON', week_type='WD')
        
        from django.test import Client
        
        # Get session for sender
        client_sender = Client()
        client_sender.login(email='sender@example.com', password='pass12345')
        sessionid_sender = client_sender.cookies.get('sessionid').value

        # Get session for recipient
        client_recipient = Client()
        client_recipient.login(email='recipient@example.com', password='pass12345')
        sessionid_recipient = client_recipient.cookies.get('sessionid').value

        async def run_flow():
            # Connect recipient to notifications
            notif_path = "/ws/notifications/"
            notif_headers = [(b"cookie", f"sessionid={sessionid_recipient}".encode())]
            comm_notif = WebsocketCommunicator(application, notif_path)
            comm_notif.scope['headers'] = notif_headers
            connected_n, _ = await comm_notif.connect()
            assert connected_n, "Notification WS failed to connect"

            # Connect sender to conversation
            chat_path = f"/ws/student/{student.pk}/"
            chat_headers = [(b"cookie", f"sessionid={sessionid_sender}".encode())]
            comm_chat = WebsocketCommunicator(application, chat_path)
            comm_chat.scope['headers'] = chat_headers
            connected_c, _ = await comm_chat.connect()
            assert connected_c, "Chat WS failed to connect"
            await comm_chat.receive_json_from() # init

            # Send message with mention
            await comm_chat.send_json_to({"action": "send", "message": "Hello @Recipient"})
            
            # Read chat echo first (to ensure processing)
            await comm_chat.receive_json_from() 

            # Check if recipient got notification
            notif_msg = await comm_notif.receive_json_from()
            assert notif_msg.get('action') == 'notification_update'
            assert 'You were mentioned by Sender' in notif_msg['notification']['content']

            await comm_chat.disconnect()
            await comm_notif.disconnect()

        asyncio.run(run_flow())

class ConversationHTTPTests(TestCase):
    def test_http_send_and_messages_endpoints(self):
        User = get_user_model()
        user = User.objects.create_user(email='http@test.com', name='HTTP Tester', role='staff', password='pass12345')
        student = Student.objects.create(first_name='HTTP', last_name='User', email='http@example.com', mode_of_class='ON', week_type='WD')
        client = self.client
        client.login(username='http@test.com', password='pass12345')
        from django.urls import reverse
        send_url = reverse('conversation_send', args=[student.pk])
        resp = client.post(send_url, {'message': 'Hello via HTTP'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data['message']['message'], 'Hello via HTTP')
        messages_url = reverse('conversation_messages', args=[student.pk])
        resp2 = client.get(messages_url)
        self.assertEqual(resp2.status_code, 200)
        msgs = resp2.json().get('messages', [])
        self.assertTrue(any(m.get('message') == 'Hello via HTTP' for m in msgs))
