from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import datetime
from .models import StudentConversation, ConversationMessage, Student
from .serializers import message_to_dict

ALLOWED_POST_ROLES = {'admin', 'staff', 'batch_coordination', 'consultant', 'trainer'}
ALLOWED_HASHTAGS = {'placement', 'class', 'payment'}
ALLOWED_PRIORITIES = {'high', 'medium', 'low'}

class StudentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.student_id = self.scope['url_route']['kwargs']['student_id']
        self.group_name = f"student_{self.student_id}"
        try:
            user = self.scope.get("user", AnonymousUser())
            print(f"WS CONNECT student={self.student_id} user={getattr(user, 'email', None)} role={getattr(user, 'role', None)}")
            
            # Mark conversation as read (reset unread count) and broadcast update
            # Only if user is an admin/staff (not the student themselves)
            is_admin = False
            if user.is_authenticated:
                role = getattr(user, 'role', '')
                if user.is_superuser or user.is_staff or role in ALLOWED_POST_ROLES:
                    is_admin = True

            if is_admin:
                unread_reset = await self.mark_conversation_read(user)
                if unread_reset:
                     await self.channel_layer.group_send(
                        "student_remarks", 
                        {
                            "type": "broadcast", 
                            "payload": {
                                "action": "remarks_list_update", 
                                "student_id": int(self.student_id),
                                "unread_count": 0,
                                "is_read_update": True
                            }
                        }
                    )
                
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
        user = self.scope.get("user", AnonymousUser())
        action = content.get("action")
        
        if action == "send":
            message_text = str(content.get("message", "")).strip()
            if not message_text:
                await self.send_json({"action": "error", "reason": "empty"})
                return
            if not await self.can_post(user):
                await self.send_json({"action": "error", "reason": "unauthorized"})
                return
            hashtag = str(content.get("hashtag", "") or "").strip().lower()
            priority = str(content.get("priority", "") or "").strip().lower()
            if hashtag not in ALLOWED_HASHTAGS:
                hashtag = ""
            if priority not in ALLOWED_PRIORITIES:
                priority = ""
            try:
                print(f"WS SEND student={self.student_id} by={getattr(user, 'email', None)} role={getattr(user, 'role', None)} len={len(message_text)}")
            except Exception:
                pass
            msg, fb, conv_stats = await self.create_message(user, message_text, hashtag, priority)
            
            # Automatically mark as read by sender
            await self.mark_message_read(msg.id, user)
            
            payload = {"action": "new_message", "message": message_to_dict(msg)}
            await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": payload})
            try:
                list_payload = {
                    "action": "remarks_list_update", 
                    "student_id": int(self.student_id), 
                    "message": message_to_dict(msg),
                    "unread_count": conv_stats.get("unread_count", 0),
                    "is_priority": conv_stats.get("is_priority", False),
                    "priority_level": conv_stats.get("priority_level", 0)
                }
                await self.channel_layer.group_send("student_remarks", {"type": "broadcast", "payload": list_payload})
            except Exception:
                pass
            if fb:
                fb_payload = {"action": "feedback_updated", "feedback": fb.get("feedback",""), "updated_by_name": fb.get("updated_by_name",""), "updated_at": fb.get("updated_at","")}
                await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": fb_payload})

        elif action == "edit_message":
            msg_id = content.get("message_id")
            new_text = str(content.get("new_text", "")).strip()
            if not msg_id or not new_text:
                return
            
            success, msg = await self.update_message(msg_id, user, new_text)
            if success and msg:
                payload = {"action": "message_updated", "message": message_to_dict(msg)}
                await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": payload})

        elif action == "mark_conversation_read":
            if user.is_authenticated:
                role = getattr(user, 'role', '')
                is_admin = user.is_superuser or user.is_staff or role in ALLOWED_POST_ROLES
                
                if is_admin:
                    unread_reset = await self.mark_conversation_read(user)
                    # Even if count didn't change (was 0), we might have marked new messages as read
                    # So we should broadcast the list update to ensure UI is consistent
                    await self.channel_layer.group_send(
                        "student_remarks", 
                        {
                            "type": "broadcast", 
                            "payload": {
                                "action": "remarks_list_update", 
                                "student_id": int(self.student_id),
                                "unread_count": 0,
                                "is_read_update": True
                            }
                        }
                    )
            else:
                await self.send_json({"action": "error", "reason": "edit_failed"})

        elif action == "mark_read":
            msg_ids = content.get("message_ids", [])
            if not msg_ids:
                return
            
            updated_msgs = []
            for mid in msg_ids:
                if await self.mark_message_read(mid, user):
                    updated_msgs.append(mid)
            
            if updated_msgs:
                # Get the updated read status for these messages to broadcast
                # For simplicity, we can just broadcast that these messages were read by this user
                # and let the frontend update the local state.
                # However, sending the full message object or just the read info is better.
                read_info = {
                    "user": getattr(user, "name", None) or getattr(user, "email", "Unknown"),
                    "read_at": datetime.now().isoformat()
                }
                payload = {
                    "action": "messages_read",
                    "message_ids": updated_msgs,
                    "read_by": read_info
                }
                await self.channel_layer.group_send(self.group_name, {"type": "broadcast", "payload": payload})

    async def broadcast(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def can_post(self, user):
        return getattr(user, "is_authenticated", False)

    @database_sync_to_async
    def mark_conversation_read(self, user):
        try:
            from .models import MessageReadStatus
            conv = StudentConversation.objects.get(student_id=self.student_id)
            unread_reset = False
            
            # Reset unread count
            if conv.unread_count > 0:
                conv.unread_count = 0
                conv.save()
                unread_reset = True

            # Mark all messages as read for this user
            unread_msgs = ConversationMessage.objects.filter(conversation=conv).exclude(read_statuses__user=user)
            new_reads = []
            for msg in unread_msgs:
                new_reads.append(MessageReadStatus(message=msg, user=user))
            
            if new_reads:
                MessageReadStatus.objects.bulk_create(new_reads)
                
            return unread_reset
        except Exception as e:
            print(f"Error marking conversation read: {e}")
            return False

    @database_sync_to_async
    def get_initial_messages(self):
        try:
            student = Student.objects.get(pk=int(self.student_id))
        except (Student.DoesNotExist, ValueError, TypeError):
            return []
        conv, _ = StudentConversation.objects.get_or_create(student=student)
        qs = conv.messages.select_related("sender").prefetch_related("read_statuses__user").order_by("-created_at")[:50]
        return [message_to_dict(m) for m in reversed(list(qs))]

    @database_sync_to_async
    def create_message(self, user, message_text, hashtag, priority):
        conv, _ = StudentConversation.objects.get_or_create(student_id=self.student_id)
        msg = ConversationMessage.objects.create(
            conversation=conv,
            sender=user if getattr(user, "is_authenticated", False) else None,
            sender_role=getattr(user, "role", "") or "",
            hashtag=hashtag or "",
            priority=priority or "",
            message=message_text
        )
        # Reload conversation to get updated stats from signal
        conv.refresh_from_db()
        conv_stats = {
            "unread_count": conv.unread_count,
            "is_priority": conv.is_priority,
            "priority_level": conv.priority_level
        }
        
        try:
            from .models import apply_feedback_from_message
            fb = apply_feedback_from_message(msg, user=user)
        except Exception:
            fb = None
        return msg, fb, conv_stats

    @database_sync_to_async
    def update_message(self, msg_id, user, new_text):
        try:
            msg = ConversationMessage.objects.get(pk=msg_id)
            if msg.sender != user:
                return False, None
            
            msg.message = new_text
            msg.is_edited = True
            msg.edited_at = timezone.now()
            msg.save()
            return True, msg
        except ConversationMessage.DoesNotExist:
            return False, None

    @database_sync_to_async
    def mark_message_read(self, msg_id, user):
        if not user or not user.is_authenticated:
            return False
        
        try:
            from .models import MessageReadStatus
            msg = ConversationMessage.objects.get(pk=msg_id)
            # Check if already read
            if MessageReadStatus.objects.filter(message=msg, user=user).exists():
                return False
            
            MessageReadStatus.objects.create(message=msg, user=user)
            return True
        except Exception:
            return False

class StudentRemarksConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = "student_remarks"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"action": "remarks_init"})
        try:
            user = self.scope.get("user", AnonymousUser())
            print(f"WS REMARKS CONNECT user={getattr(user, 'email', None)} role={getattr(user, 'role', None)}")
        except Exception:
            pass

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast(self, event):
        try:
            payload = event.get("payload", {})
            print(f"WS REMARKS OUT action={payload.get('action')} student_id={payload.get('student_id')}")
        except Exception:
            pass
        await self.send_json(event["payload"])
