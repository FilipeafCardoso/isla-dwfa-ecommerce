from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_gestor(user):
    return user.is_authenticated and user.groups.filter(name="gestores").exists()


class IsGestor(BasePermission):
    def has_permission(self, request, view):
        return is_gestor(request.user)


class IsGestorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # catálogo público
        return is_gestor(request.user)


class IsOwnerOrGestor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_gestor(request.user) or obj.customer.user_id == request.user.id
