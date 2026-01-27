from .models import ConversationMessage

def message_to_dict(msg: ConversationMessage):
    return {
        "id": msg.id,
        "sender": getattr(msg.sender, "name", None) or getattr(msg.sender, "email", "System") if msg.sender else "System",
        "sender_role": msg.sender_role,
        "hashtag": getattr(msg, "hashtag", "") or "",
        "priority": getattr(msg, "priority", "") or "",
        "message": msg.message,
        "created_at": msg.created_at.isoformat(),
        "type": msg.message_type,
        "file_url": msg.file.url if msg.file else None,
        "file_name": msg.file_name,
        "file_size": msg.file_size,
        "file_mime": msg.file_mime,
        "is_edited": msg.is_edited,
        "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
        "read_by": [
            {
                "user": getattr(status.user, "name", None) or getattr(status.user, "email", "Unknown"),
                "read_at": status.read_at.isoformat()
            }
            for status in msg.read_statuses.all()
        ]
    }
