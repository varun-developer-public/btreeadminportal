from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from .models import Student, StudentConversation, ConversationMessage
from channels.testing import WebsocketCommunicator
from core.asgi import application
import asyncio

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
