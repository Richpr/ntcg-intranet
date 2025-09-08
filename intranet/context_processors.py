# Fichier : intranet/context_processors.py

from .models import Notification

def is_rh_group(request):
    is_rh = request.user.groups.filter(name='Ressources Humaines').exists()
    return {'is_rh': is_rh}

def is_project_coordinator(request):
    is_coordinator = request.user.groups.filter(name='Coordinateurs de Projets').exists()
    return {'is_coordinator': is_coordinator}

def unread_notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        unread_count = 0
    return {'unread_notifications_count': unread_count}