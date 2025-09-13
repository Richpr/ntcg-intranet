# intranet/templatetags/intranet_tags.py

from django import template
from django.contrib.auth.models import Group
from ..models import Site, Task

register = template.Library()



@register.filter
def get_total_tasks(sites_queryset):
    """
    Calcule le nombre total de tâches pour une liste de sites.
    """
    total = 0
    for site in sites_queryset:
        total += site.tasks.count()
    return total

@register.filter(name='has_group')
def has_group(user, group_name):
    if user.is_authenticated:
        # Debug: afficher ce qui est vérifié
        # print(f"Vérification groupe: {group_name} pour {user}")
        groups = user.groups.all()
        # print(f"Groupes de l'utilisateur: {[g.name for g in groups]}")
        result = user.groups.filter(name=group_name).exists()
        # print(f"Résultat: {result}")
        return result
    return False

@register.filter(name='get_total_tasks')
def get_total_tasks(sites):
    return sum(site.tasks.count() for site in sites)