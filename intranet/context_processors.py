from django.utils.functional import SimpleLazyObject
from .models import Notification

def user_groups(request):
    if request.user.is_authenticated:
        # Récupère tous les groupes une seule fois
        group_names = list(request.user.groups.values_list('name', flat=True))
        return {
            'user_groups': group_names,
            'is_rh': 'Ressources Humaines' in group_names,
            'is_coordinator': 'Coordinateur de Projet' in group_names,
            'is_country_manager': 'Country Manager' in group_names,
            'is_team_lead': 'Team Lead' in group_names,
        }
    return {
        'user_groups': [],
        'is_rh': False,
        'is_coordinator': False,
        'is_country_manager': False,
        'is_team_lead': False,
    }

def unread_notifications(request):
    if request.user.is_authenticated:
        # CORRECTION ICI : utiliser 'user' au lieu de 'recipient'
       unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        unread_count = 0
    return {'unread_notifications_count': unread_count}