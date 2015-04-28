from rest_framework.permissions import BasePermission, SAFE_METHODS

__all__ = [
    'AuthenticatedReadOnly',
    'OnlyAdminCanDelete',
    'CreateOnly',
]


class AuthenticatedReadOnly(BasePermission):
    """
    Read-only, but only for authenticated users.
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'OPTIONS':
            return True
        if request.method in SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            from permissions import UserSerializer
            if view.serializer_class == UserSerializer:
                if obj == request.user:
                    return True
                return False
            return True
        return False

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        if request.method in SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            return True
        return False


class CreateOnly(BasePermission):
    """
    This object is
    * Creatable by authenticated users
    * Readable by everyone
    * Editable by nobody
    * Deletable by staff
    """
    def has_object_permission(self, request, view, obj):
        if request.method == 'OPTIONS':
            return True
        if request.method == 'DELETE' and \
                request.user and request.user.is_staff:
            return True
        if request.method in SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            return True
        # PUT is not supported
        return False

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        if request.method == 'POST' and \
                request.user and request.user.is_authenticated():
            return True
        if request.method in SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            return True
        # PATCH is not supported
        return False


class OnlyAdminCanDelete(BasePermission):
    """
    This object is:
    * Creatable by authenticated users
    * Editable by authenticated owner
    * Deletable only by admin

    Note: requires model have 'owner' FK of django User type.
    """

    def has_object_permission(self, request, view, obj):
        if request.method == 'OPTIONS':
            return True
        if request.method in permissions.SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            return True
        if request.method == 'DELETE' and \
                request.user and request.user.is_staff:
            return True
        if reuqest.method == 'PUT' and \
                request.user and request.user.is_authenticated() and \
                request.user == obj.owner:
            return True
        return False

    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        if request.method in permissions.SAFE_METHODS and \
                request.user and request.user.is_authenticated():
            return True
        if request.method == 'POST' and \
                request.user and request.user.is_authenticated():
            return True
        # PATCH not supported
        return False
