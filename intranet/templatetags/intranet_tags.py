# intranet/templatetags/intranet_tags.py

from django import template
from django.contrib.auth.models import Group
from ..models import Site, Task

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Vérifie si un utilisateur appartient à un groupe spécifique.
    """
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False
    return group in user.groups.all()

@register.filter
def get_total_tasks(sites_queryset):
    """
    Calcule le nombre total de tâches pour une liste de sites.
    """
    total = 0
    for site in sites_queryset:
        total += site.tasks.count()
    return total