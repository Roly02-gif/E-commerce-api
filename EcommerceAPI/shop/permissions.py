from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    - lecture autorisée à tout le monde (GET, HEAD, OPTIONS)
    - écriture réservée aux admins (POST, PUT, PATCH, DELETE)
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
