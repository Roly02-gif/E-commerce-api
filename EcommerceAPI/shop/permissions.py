from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - read-only for everyone (GET, HEAD, OPTIONS)
    - write permissions only for admins (POST, PUT, PATCH, DELETE)
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    - admin can do anything.
    - authenticated user can only see and modify their own account.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return view.action in [
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.pk == request.user.pk
