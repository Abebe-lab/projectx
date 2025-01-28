# decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.apps import apps
from organogram.models import Permission, RolePermission
UserRole = apps.get_model('organogram', 'UserRole')

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if UserRole.objects.filter(user=user, role__name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                return redirect('access_denied')  # Redirect to access denied page or handle unauthorized access
        return wrapper
    return decorator


def permission_required(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            user_roles = UserRole.objects.filter(user=user)
            c_permission = Permission.objects.get(display_name=permission)
            for user_role in user_roles:
                if user_role:
                    if RolePermission.objects.filter(role=user_role.role, permission=c_permission).exists():
                        return view_func(request, *args, **kwargs)
                    else:
                        return redirect('access_denied')
        return wrapper
    return decorator
