from .models import ConversationMessage

def message_to_dict(msg: ConversationMessage):
    return {
        "id": msg.id,
        "sender": getattr(msg.sender, "name", None) or getattr(msg.sender, "email", "System") if msg.sender else "System",
        "sender_role": msg.sender_role,
        "message": msg.message,
        "created_at": msg.created_at.isoformat(),
    }
