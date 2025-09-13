from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group


HR_GROUP = 'Ressources Humaines'
COORDINATOR_GROUP = 'Coordinateur de Projet'

def hr_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe 'Ressources Humaines'.
    """
    def wrapper_func(request, *args, **kwargs):
        if request.user.groups.filter(name='Ressources Humaines').exists():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper_func

def country_manager_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe 'Country Manager'.
    """
    def wrapper_func(request, *args, **kwargs):
        group_name = 'Country Manager'
        if request.user.groups.filter(name=group_name).exists():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper_func

def coordinator_required(view_func):
    """
    Décorateur pour restreindre l'accès aux utilisateurs du groupe 'Coordinateur de Projet'.
    """
    def wrapper_func(request, *args, **kwargs):
        group_name = 'Coordinateur de Projet'
        if request.user.groups.filter(name=group_name).exists():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper_func

def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied(f"Accès réservé au groupe {group_name}")
        return wrapper
    return decorator