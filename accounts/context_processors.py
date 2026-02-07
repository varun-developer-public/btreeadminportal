from .utils import get_unread_mentions

def user_notifications(request):
    if request.user.is_authenticated:
        return {'unread_notifications': get_unread_mentions(request.user)}
    return {'unread_notifications': []}
