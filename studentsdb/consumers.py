from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import StudentConversation, ConversationMessage, Student
from .serializers import message_to_dict

ALLOWED_POST_ROLES = {'admin', 'staff', 'batch_coordination', 'consultant', 'trainer'}

class StudentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.student_id = self.scope['url_route']['kwargs']['student_id']
        self.group_name = f"student_{self.student_id}"
        try:
            user = self.scope.get("user", AnonymousUser())
            print(f"WS CONNECT student={self.student_id} user={getattr(user, 'email', None)} role={getattr(user, 'role', None)}")
        except Exception as e:
            print(f"WS CONNECT ERROR student={self.student_id}: {e}")
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        messages = await self.get_initial_messages()
        await self.send_json({"action": "init", "messages": messages})

    async def disconnect(self, code):
        try:
            print(f"WS DISCONNECT student={self.student_id} code={code}")
        except Exception:
            pass
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        if content.get("action") == "send":
            user = self.scope.get("user", AnonymousUser())
            message_text = str(content.get("message", "")).strip()
            if not message_text:
                await self.send_json({"action": "error", "reason": "empty"})
                return
            if not await self.can_post(user):
                await self.send_json({"action": "error", "reason": "unauthorized"})
                return
            try:
                print(f"WS SEND student={self.student_id} by={getattr(user, 'email', None)} role={getattr(user, 'role', None)} len={len(message_text)}")
            except Exception:
                pass
            msg, fb = await self.create_message(user, message_text)
            payload = {"action": "new_message", "message": message_to_dict(msg)}
            await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": payload})
            if fb:
                fb_payload = {"action": "feedback_updated", "feedback": fb.get("feedback",""), "updated_by_name": fb.get("updated_by_name",""), "updated_at": fb.get("updated_at","")}
                await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": fb_payload})

    async def broadcast(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def can_post(self, user):
        if not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_superuser", False):
            return True
        role = getattr(user, "role", None)
        return role in ALLOWED_POST_ROLES

    @database_sync_to_async
    def get_initial_messages(self):
        try:
            student = Student.objects.get(pk=int(self.student_id))
        except (Student.DoesNotExist, ValueError, TypeError):
            return []
        conv, _ = StudentConversation.objects.get_or_create(student=student)
        qs = conv.messages.select_related("sender").order_by("-created_at")[:50]
        return [message_to_dict(m) for m in reversed(list(qs))]

    @database_sync_to_async
    def create_message(self, user, message_text):
        conv, _ = StudentConversation.objects.get_or_create(student_id=self.student_id)
        msg = ConversationMessage.objects.create(
            conversation=conv,
            sender=user if getattr(user, "is_authenticated", False) else None,
            sender_role=getattr(user, "role", "") or "",
            message=message_text
        )
        try:
            from .models import apply_feedback_from_message
            fb = apply_feedback_from_message(msg, user=user)
        except Exception:
            fb = None
        return msg, fb
