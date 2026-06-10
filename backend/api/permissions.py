from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Only admins (staff users) can access"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admins can do anything
    Non-admins can only read
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """Only owner or admin can modify"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.created_by == request.user
