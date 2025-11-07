from rest_framework.permissions import BasePermission

class IsBatchCoordinator(BasePermission):
    """
    Allows access only to users with the 'batch_coordination' role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'batch_coordination' or request.user.is_superuser)
class IsStaff(BasePermission):
    """
    Allows access only to users with the 'staff' role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'staff' or request.user.is_superuser)

class IsTrainer(BasePermission):
    """
    Allows access only to users with the 'trainer' role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'trainer' or request.user.is_superuser)
