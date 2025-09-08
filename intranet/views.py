# Fichier : intranet/views.py
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q, Count, Sum
from django.urls import reverse 
from .models import User, Department
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.messages import success, error
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.template.defaultfilters import slugify
from wkhtmltopdf.views import PDFTemplateResponse
from .forms import SimplifiedEmployeeRegistrationForm, ProfileUpdateForm, DocumentUploadForm
from .decorators import hr_required
from .models import Document, Post, ProfileUpdate, BadgeDefinition, EmployeeBadge, Country
import os
from datetime import datetime, date
from django.db import models
from django.core.files.base import ContentFile
import datetime
from datetime import datetime, date
from django.db.models import ForeignKey
from weasyprint import HTML
from .forms import DocumentRequestForm
from .models import DocumentRequest, DocumentType
from .models import LeaveRequest, LeaveType
from .forms import LeaveRequestForm, LeaveRequestHRForm
from .models import Payslip, PayPeriod, User
from .forms import PayslipForm, PayPeriodForm
from django.db.models import F
from datetime import datetime, timedelta, date
from collections import defaultdict
from .models import Notification
from .forms import ProjectForm, SiteForm
from .models import Project, Site, Task
from django.core.exceptions import PermissionDenied
from .forms import TaskForm
from django.db import transaction # Importez cette ligne
from django.core.files.base import ContentFile
import json # Assurez-vous d'importer ce module
import datetime
from django.utils import timezone 
from datetime import date, timedelta
from datetime import datetime
from .models import ProfileUpdate, User  # Assure-toi que le modèle User est importé
from django.contrib.auth.decorators import login_required
from .models import User, Department
from .decorators import hr_required, country_manager_required, coordinator_required
# Référence sécurisée à votre modèle d'utilisateur
User = get_user_model()

@login_required
@hr_required
@login_required
@hr_required
def employee_directory(request):
    """
    Vue pour afficher l'annuaire des employés avec pagination et requêtes optimisées,
    avec une logique de filtrage par pays, département, statut et recherche textuelle.
    """
    user = request.user

    # Récupération des paramètres de l'URL pour les filtres
    selected_country_code = request.GET.get('country')
    selected_department = request.GET.get('department')
    selected_status = request.GET.get('status')
    search_query = request.GET.get('search')
    
    countries_to_filter = []
    countries_available = []

    # Logique pour les permissions d'accès aux pays
    if user.is_superuser:
        countries_available = Country.objects.filter(is_active=True).order_by('name')
        if selected_country_code:
            countries_to_filter = [selected_country_code]
        else:
            countries_to_filter = [c.code for c in countries_available]
    elif user.groups.filter(name='RH').exists(): 
        countries_available = user.managed_countries.filter(is_active=True).order_by('name')
        if selected_country_code and selected_country_code in [c.code for c in countries_available]:
            countries_to_filter = [selected_country_code]
        else:
            countries_to_filter = [c.code for c in countries_available]
    else:
        selected_country_code = user.country.code if user.country else None
        if selected_country_code:
            countries_to_filter = [selected_country_code]
        countries_available = []

    # Création de la requête de base
    employees_list = User.objects.all()

    # Application des filtres
    if countries_to_filter:
        employees_list = employees_list.filter(country__code__in=countries_to_filter)
    
    if selected_department:
        employees_list = employees_list.filter(departement__name=selected_department)
    
    if selected_status == 'active':
        employees_list = employees_list.filter(is_active=True)
    elif selected_status == 'inactive':
        employees_list = employees_list.filter(is_active=False)

    # Recherche textuelle
    if search_query:
        employees_list = employees_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(job_role__name__icontains=search_query) |
            Q(professional_email__icontains=search_query)
        )

    # Correction de l'erreur dans la pré-récupération
    employees_list = employees_list.select_related(
        'departement',
        'job_role', 
        'bank_info', 
        'country'
    ).prefetch_related('received_badges').order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(employees_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Récupérer tous les départements pour le filtre
    departments = Department.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'countries': countries_available,
        'selected_country': selected_country_code,
        'departments': departments,
        'selected_department': selected_department,
        'selected_status': selected_status,
        'search_query': search_query,
    }
    return render(request, 'intranet/employee_directory.html', context)


def create_notification(user, title, message, notification_type='info'):
    """Crée et enregistre une notification pour un utilisateur."""
    from .models import Notification
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type
    )

@login_required
def home_view(request):
    latest_posts = Post.objects.all().order_by('-created_at')[:5]
    is_hr = request.user.groups.filter(name='RH').exists()
    
    # Calcul des années de service
    if hasattr(request.user, 'years_of_service'):
        years_of_service = request.user.years_of_service
    else:
        years_of_service = 0
    
    # Context de base
    context = {
        'latest_posts': latest_posts,
        'is_hr': is_hr,
        'years_of_service': years_of_service,
    }
    
    # Statistiques personnelles
    context.update({
        'my_documents_count': request.user.documents.count(),
        'my_leave_requests_count': request.user.leave_requests.count(),
        'pending_documents_count': request.user.document_requests.filter(status='PENDING').count(),
        'pending_updates_count': request.user.profile_updates.filter(status='pending').count(),
        'unread_notifications_count': request.user.notifications.filter(is_read=False).count(),
    })
    
    # Données pour les RH
    if is_hr:
        context['hr_stats'] = get_hr_statistics()
    
    # Événements à venir (simulés - à remplacer par un vrai modèle)
    context['events'] = get_upcoming_events()
    
    # Notifications récentes
    context['recent_notifications'] = request.user.notifications.all().order_by('-created_at')[:5]
    
    return render(request, 'intranet/home.html', context)



def get_hr_statistics():
    """Retourne les statistiques pour le tableau de bord RH"""
    today = datetime.now().date()
    
    start_of_month = today.replace(day=1)
    
    return {
        'total_employees': User.objects.count(),
        'active_employees': User.objects.filter(is_active=True).count(),
        'new_this_month': User.objects.filter(date_joined__gte=start_of_month).count(),
        'pending_updates': ProfileUpdate.objects.filter(status='pending').count(),
        'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
        'pending_documents': DocumentRequest.objects.filter(status='PENDING').count(),
    }

def get_upcoming_events():
    """Retourne les événements à venir (simulés)"""
    today = datetime.now().date()
    return [
        {
            'title': 'Team-building annuel',
            'date': today + timedelta(days=5),
            'time': '09:00 - 18:00',
            'location': 'Siège social',
            'type': 'success'
        },
        {
            'title': 'Formation cybersécurité',
            'date': today + timedelta(days=12),
            'time': '14:00 - 17:00',
            'location': 'Salle de formation',
            'type': 'info'
        },
        {
            'title': 'Réunion départementale',
            'date': today + timedelta(days=3),
            'time': '10:00 - 12:00',
            'location': 'Salle de réunion A',
            'type': 'warning'
        }
    ]

@login_required
@hr_required
def employee_bank_info(request):
    """
    Affiche un tableau avec les informations bancaires des employés.
    Accessible uniquement au groupe 'Ressources Humaines'.
    """
    employees = User.objects.all().order_by('last_name')
    context = {
        'employees': employees,
    }
    return render(request, 'intranet/employee_bank_info.html', context)


# Vue annuaire optimisée
@login_required
@hr_required
def employee_directory(request):
    user = request.user
    selected_country_code = request.GET.get('country')
    selected_department = request.GET.get('department')
    selected_status = request.GET.get('status')
    search_query = request.GET.get('search')
    
    countries_to_filter = []
    countries_available = []

    # Gestion des permissions par pays
    if user.is_superuser:
        countries_available = Country.objects.filter(is_active=True).order_by('name')
        if selected_country_code:
            countries_to_filter = [selected_country_code]
        else:
            countries_to_filter = [c.code for c in countries_available]
    elif user.groups.filter(name='RH').exists(): 
        countries_available = user.managed_countries.filter(is_active=True).order_by('name')
        if selected_country_code and selected_country_code in [c.code for c in countries_available]:
            countries_to_filter = [selected_country_code]
        else:
            countries_to_filter = [c.code for c in countries_available]
    else:
        selected_country_code = user.country.code if user.country else None
        if selected_country_code:
            countries_to_filter = [selected_country_code]
        countries_available = []

    # Construction de la requête
    employees_list = User.objects.all()
    
    # Application des filtres
    if countries_to_filter:
        employees_list = employees_list.filter(country__code__in=countries_to_filter)
    
    if selected_department:
        employees_list = employees_list.filter(departement__name=selected_department)
    
    if selected_status == 'active':
        employees_list = employees_list.filter(is_active=True)
    elif selected_status == 'inactive':
        employees_list = employees_list.filter(is_active=False)

    # Recherche textuelle
    if search_query:
        employees_list = employees_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(job_role__name__icontains=search_query) |
            Q(professional_email__icontains=search_query)
        )

    # Optimisation des requêtes
    employees_list = employees_list.select_related(
        'departement', 'job_role', 'bank_info', 'country'
    ).prefetch_related('received_badges').order_by('last_name', 'first_name')

    # Pagination
    paginator = Paginator(employees_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques
    total_employees = employees_list.count()
    active_employees = employees_list.filter(is_active=True).count()

    context = {
        'page_obj': page_obj,
        'countries': countries_available,
        'selected_country': selected_country_code,
        'departments': Department.objects.all().order_by('name'),
        'selected_department': selected_department,
        'selected_status': selected_status,
        'search_query': search_query,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': total_employees - active_employees,
    }
    return render(request, 'intranet/employee_directory.html', context)

# Tableau de bord RH
@login_required
@hr_required
def hr_dashboard(request):
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Statistiques de base
    stats = {
        'total_employees': User.objects.count(),
        'active_employees': User.objects.filter(is_active=True).count(),
        'new_this_month': User.objects.filter(date_joined__gte=start_of_month).count(),
        'pending_updates': ProfileUpdate.objects.filter(status='pending').count(),
        'pending_leaves': LeaveRequest.objects.filter(status='PENDING').count(),
        'pending_documents': DocumentRequest.objects.filter(status='PENDING').count(),
    }
    
    # Statistiques par département
    departments_stats = Department.objects.annotate(
        employee_count=Count('user'),
        active_count=Count('user', filter=Q(user__is_active=True))
    )
    
    # Évolution mensuelle
    monthly_stats = []
    for i in range(6):
        month_date = start_of_month - timedelta(days=30*i)
        count = User.objects.filter(
            date_joined__month=month_date.month, 
            date_joined__year=month_date.year
        ).count()
        monthly_stats.append({
            'month': month_date.strftime('%b %Y'), 
            'count': count
        })
    
    # Documents les plus demandés
    popular_documents = DocumentType.objects.annotate(
        request_count=Count('requests')
    ).order_by('-request_count')[:5]

    context = {
        'stats': stats,
        'departments_stats': departments_stats,
        'monthly_stats': monthly_stats,
        'popular_documents': popular_documents,
        'title': 'Tableau de bord RH'
    }
    
    return render(request, 'intranet/hr_dashboard.html', context)


def create_notification(user, title, message, notification_type='info', link=None):
    """Crée et enregistre une notification pour un utilisateur."""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link  # Nouveau champ pour stocker un lien
    )
    return notification

# Gestion des notifications
@login_required
def notifications_view(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Marquer toutes comme lues
        notifications.update(is_read=True)
        return JsonResponse({'status': 'success'})
    
    context = {
        'notifications': notifications,
        'title': 'Mes notifications'
    }
    return render(request, 'intranet/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(
            request.user.notifications, 
            id=notification_id
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

# API pour les statistiques
@login_required
def api_statistics(request):
    if not request.user.groups.filter(name='RH').exists():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Statistiques pour les graphiques
    leave_stats = LeaveRequest.objects.values('status').annotate(
        count=Count('id')
    )
    
    document_stats = DocumentRequest.objects.values('status').annotate(
        count=Count('id')
    )
    
    return JsonResponse({
        'leave_stats': list(leave_stats),
        'document_stats': list(document_stats),
    })

@login_required
def api_statistics(request):
    """
    Retourne le nombre de notifications non lues pour l'utilisateur connecté.
    """
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'unread_notifications_count': unread_count})






def profile_view(request, user_id=None):
    """
    Vue pour afficher le profil de l'utilisateur connecté ou d'un employé spécifique.
    """
    if user_id:
        employee = get_object_or_404(User, pk=user_id)
    else:
        employee = request.user
    
    documents = employee.documents.all()
    employee_badges = employee.received_badges.all()
    updates = ProfileUpdate.objects.filter(user=employee).order_by('-submitted_at')

    # Récupérer tous les badges possibles
    all_badge_definitions = BadgeDefinition.objects.all()
    
    # Récupérer les IDs des badges de l'employé pour une vérification rapide dans le template
    employee_badge_ids = employee_badges.values_list('badge__id', flat=True)

    context = {
        'employee': employee,
        'documents': documents,
        'employee_badges': employee_badges,
        'updates': updates,
        'all_badge_definitions': all_badge_definitions,
        'employee_badge_ids': employee_badge_ids,
    }
    return render(request, 'intranet/profile.html', context)


@login_required
@hr_required
def register_employee(request):
    """
    Vue pour enregistrer un nouvel employé, accessible uniquement aux RH.
    Utilise un formulaire simplifié pour la création initiale.
    """
    if request.method == 'POST':
        form = SimplifiedEmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # La méthode save() du formulaire gère maintenant tout
            
            # Attribuer un groupe à l'employé
            try:
                employee_group = Group.objects.get(name='Employés')
                user.groups.add(employee_group)
            except Group.DoesNotExist:
                messages.warning(request, "Le groupe 'Employés' n'existe pas. Veuillez le créer dans l'administration.")
            
            temp_password = form.temp_password
            messages.success(request, f"Le compte de {user.get_full_name()} a été créé avec succès.<br>Nom d'utilisateur : **{user.username}**<br>Mot de passe temporaire : **{temp_password}**")
            return redirect('employee_directory')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = SimplifiedEmployeeRegistrationForm()
        
    context = {
            'form': form,
            'title': 'Enregistrer un employé'
        }
    return render(request, 'intranet/register_employee.html', context)


@login_required
def profile_update(request):
    """
    Vue permettant à l'utilisateur de soumettre des mises à jour de profil
    pour approbation et de télécharger des documents.
    """
    existing_update = ProfileUpdate.objects.filter(user=request.user, status='pending').first()

    if request.method == 'POST':
        # Logique de soumission du formulaire de mise à jour de profil
        if 'profile_form_submit' in request.POST:
            if existing_update:
                messages.info(request, "Une demande de mise à jour de votre profil est déjà en attente d'approbation.")
                return redirect('my_profile')
            
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            
            if profile_form.is_valid():
                updated_fields = {}
                cleaned_data = profile_form.cleaned_data

                for field, new_value in cleaned_data.items():
                    # Utilisation d'un bloc try-except pour éviter les erreurs si l'attribut n'existe pas
                    try:
                        current_value = getattr(request.user, field)
                        
                        # Gère les champs de type ForeignKey ou FileField
                        if isinstance(current_value, models.Model):
                            current_value_to_compare = current_value.pk
                        else:
                            current_value_to_compare = current_value

                        if current_value_to_compare != new_value:
                            if hasattr(new_value, 'name'):
                                # Gère les champs de type fichier (ex: photo_profil)
                                updated_fields[field] = new_value.name
                            else:
                                updated_fields[field] = new_value
                    except AttributeError:
                        # Gère le cas où le champ n'existe pas sur le modèle User (ex: si le formulaire a des champs supplémentaires)
                        pass

                if updated_fields:
                    ProfileUpdate.objects.create(
                        user=request.user,
                        updated_fields=updated_fields
                    )
                    messages.success(request, 'Votre demande de mise à jour de profil a été soumise pour approbation.')
                else:
                    messages.info(request, "Aucune modification n'a été détectée.")
                
                return redirect('my_profile')
        
        # Logique pour le formulaire de téléchargement de documents
        if 'document_form_submit' in request.POST:
            document_form = DocumentUploadForm(request.POST, request.FILES)
            if document_form.is_valid():
                new_document = document_form.save(commit=False)
                new_document.employe = request.user
                new_document.save()
                messages.success(request, f"Le document '{new_document.nom}' a été téléchargé avec succès.")
                return redirect('my_profile')

    else: # Requête GET
        # Pré-remplit le formulaire avec toutes les données de l'utilisateur
        profile_form = ProfileUpdateForm(instance=request.user)
        document_form = DocumentUploadForm()

    context = {
        'profile_form': profile_form,
        'document_form': document_form,
        'existing_update': existing_update
    }
    return render(request, 'intranet/profile_update.html', context)





def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@hr_required
def pending_updates_list(request):
    pending_updates = ProfileUpdate.objects.filter(status='pending').order_by('submitted_at')
    context = {
        'pending_updates': pending_updates
    }
    return render(request, 'intranet/pending_updates_list.html', context)


@login_required
@hr_required
def review_profile_update(request, update_id):
    profile_update = get_object_or_404(ProfileUpdate, id=update_id, status='pending')
    
    # ***IMPORTANT : Assurez-vous que le bloc `if request.method == 'POST'`
    # a été complètement supprimé de cette fonction.***
    
    user = profile_update.user
    update_data = profile_update.updated_fields
    comparison_data = []

    for field in user._meta.get_fields():
        if field.name in ['password', 'last_login', 'is_superuser', 'is_staff', 'date_joined', 'groups', 'user_permissions', 'managed_countries', 'document', 'payslip', 'notification']:
            continue
        try:
            current_value = getattr(user, field.name, None)
            new_value = update_data.get(field.name, current_value)
            if isinstance(field, models.ForeignKey):
                if current_value: current_value = str(current_value)
                if new_value:
                    try:
                        related_model = field.related_model
                        new_value = str(related_model.objects.get(name=new_value))
                    except related_model.DoesNotExist:
                        new_value = "Valeur invalide"
            if isinstance(current_value, date):
                current_value = current_value.strftime("%d/%m/%Y")
            if isinstance(new_value, str) and field.name.endswith('date'):
                try: new_value = datetime.strptime(new_value, "%Y-%m-%d").strftime("%d/%m/%Y")
                except (ValueError, TypeError): pass
            comparison_data.append({
                'field_name': field.name,
                'verbose_name': field.verbose_name.title(),
                'current_value': current_value,
                'new_value': new_value,
                'has_changed': str(current_value) != str(new_value)
            })
        except AttributeError:
            continue
    context = {'update': profile_update, 'comparison_data': comparison_data}
    return render(request, 'intranet/review_profile_update.html', context)


@login_required
@hr_required
@transaction.atomic
def approve_update(request, update_id):
    update = get_object_or_404(ProfileUpdate, id=update_id)
    user = update.user

    # Liste des champs à transférer
    fields_to_transfer = [
        'job_role', 'departement', 'date_de_naissance', 'adresse',
        'numero_de_telephone', 'sexe', 'statut_matrimonial',
        'cnss', 'dependants', 'bank_info', 'bank_account_number'
    ]

    for field_name in fields_to_transfer:
        # Utiliser getattr pour accéder à l'attribut de manière sécurisée
        field_value = getattr(update, field_name, None)
        if field_value:
            setattr(user, field_name, field_value)

    # Gérer le cas de l'image de profil
    if getattr(update, 'photo_profil', None):
        user.photo_profil.save(os.path.basename(update.photo_profil.path), update.photo_profil.file)
        update.photo_profil.delete() # Supprime le fichier temporaire
    
    # Enregistrer toutes les modifications
    user.save()
    update.delete() # Supprimer la demande une fois le profil mis à jour

    messages.success(request, "La demande de mise à jour du profil a été approuvée avec succès.")
    return redirect('pending_updates_list')


@login_required
@hr_required
@require_POST
def reject_update(request, update_id):
    update = get_object_or_404(ProfileUpdate, id=update_id, status='pending')
    
    # Récupérer les commentaires pour chaque champ
    rejection_comments = {}
    for field in update.updated_fields.keys():
        comment = request.POST.get(f'comment_{field}', '').strip()
        if comment:
            rejection_comments[field] = comment
    
    # Vérifier qu'il y a au moins un commentaire
    if not rejection_comments:
        messages.error(request, "Veuillez ajouter au moins un commentaire pour expliquer le rejet.")
        return redirect('review_profile_update', update_id=update_id)
    
    # Enregistrer les commentaires et mettre à jour le statut
    update.rejection_comments = rejection_comments
    update.status = 'rejected'
    update.approved_at = timezone.now()  # Maintenant timezone est défini
    update.save()
    
    # Créer une notification pour l'employé
    create_notification(
        update.user,
        "Mise à jour de profil rejetée",
        f"Votre demande de mise à jour de profil a été rejetée. {len(rejection_comments)} champ(s) nécessitent des corrections.",
        'warning',
        link=reverse('view_rejected_update', args=[update.id])
    )
    
    messages.error(request, f"La mise à jour de profil pour {update.user.get_full_name()} a été rejetée avec succès.")
    return redirect('pending_updates_list')


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def edit_employee(request, employee_id):
    """
    Permet de modifier les informations de base d'un employé.
    """
    employee = get_object_or_404(User, pk=employee_id)
    
    if request.method == 'POST':
        form = SimplifiedEmployeeRegistrationForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Les informations de {employee.get_full_name()} ont été mises à jour.")
            return redirect('employee_directory')
    else:
        form = SimplifiedEmployeeRegistrationForm(instance=employee)
        
    context = {
        'form': form,
        'employee': employee,
    }
    return render(request, 'intranet/edit_employee.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def delete_employee(request, employee_id):
    """
    Permet de supprimer un employé.
    """
    employee = get_object_or_404(User, pk=employee_id)
    
    if request.method == 'POST':
        employee.delete()
        messages.success(request, f"L'employé {employee.get_full_name()} a été supprimé.")
        return redirect('employee_list')
        
    context = {
        'employee': employee,
    }
    return render(request, 'intranet/delete_employee.html', context)

@login_required
def safety_passport_view(request, user_id=None):
    if user_id:
        employee = get_object_or_404(User, pk=user_id)
    else:
        employee = request.user
    
    all_badge_definitions = BadgeDefinition.objects.all()
    employee_badge_ids = employee.received_badges.values_list('badge__id', flat=True)

    context = {
        'employee': employee,
        'all_badge_definitions': all_badge_definitions,
        'employee_badge_ids': employee_badge_ids,
        'base_url': request.build_absolute_uri('/'),
        'user': request.user,
    }

    if 'download_pdf' in request.GET:
        # Utilisation de la classe PDFTemplateResponse pour générer le PDF
        response = PDFTemplateResponse(
            request=request,
            template='intranet/safety_passport.html',
            context=context,
            filename=f"Passeport_Securite_{employee.last_name}_{employee.first_name}.pdf",
            show_content_in_browser=False, # Pour forcer le téléchargement
        )
        return response

    return render(request, 'intranet/safety_passport.html', context)


@hr_required
def payslip_list(request):
    """
    Vue pour lister toutes les fiches de paie.
    """
    payslips = Payslip.objects.select_related('employee', 'pay_period').order_by('-pay_period__end_date', 'employee__last_name')
    
    context = {
        'payslips': payslips,
        'title': 'Gestion des fiches de paie'
    }
    return render(request, 'intranet/payslip_list.html', context)


@hr_required
def create_payslip(request):
    """
    Vue pour créer une nouvelle fiche de paie.
    """
    if request.method == 'POST':
        form = PayslipForm(request.POST)
        if form.is_valid():
            payslip = form.save(commit=False)
            
            # Calcul du salaire net basé sur le brut et les déductions
            # Vous pouvez ajuster cette logique pour inclure les taxes
            payslip.net_salary = payslip.gross_salary - payslip.taxes - payslip.deductions + payslip.bonuses + payslip.other_payments
            payslip.save()

            messages.success(request, f"La fiche de paie de {payslip.employee.get_full_name()} pour {payslip.pay_period.name} a été créée avec succès.")
            return redirect('payslip_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PayslipForm()
    
    context = {
        'form': form,
        'title': 'Créer une fiche de paie'
    }
    return render(request, 'intranet/payslip_form.html', context)


@hr_required
def edit_payslip(request, payslip_id):
    """
    Vue pour modifier une fiche de paie existante.
    """
    payslip = get_object_or_404(Payslip, pk=payslip_id)
    
    if request.method == 'POST':
        form = PayslipForm(request.POST, instance=payslip)
        if form.is_valid():
            updated_payslip = form.save(commit=False)
            updated_payslip.net_salary = updated_payslip.gross_salary - updated_payslip.taxes - updated_payslip.deductions + updated_payslip.bonuses + updated_payslip.other_payments
            updated_payslip.save()
            messages.success(request, f"La fiche de paie pour {updated_payslip.employee.get_full_name()} a été mise à jour.")
            return redirect('payslip_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PayslipForm(instance=payslip)
        
    context = {
        'form': form,
        'title': 'Modifier une fiche de paie'
    }
    return render(request, 'intranet/payslip_form.html', context)

@login_required
def submit_leave_request(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user
            leave_request.save()
            messages.success(request, "Votre demande de congé a été soumise avec succès.")
            return redirect('home_view') # Rediriger l'employé vers la page d'accueil
    else:
        form = LeaveRequestForm()
    
    context = {
        'form': form,
        'title': 'Soumettre une demande de congé'
    }
    return render(request, 'intranet/submit_leave_request.html', context)

@hr_required
def manage_leave_requests(request):
    pending_requests = LeaveRequest.objects.filter(status='PENDING').order_by('created_at')
    processed_requests = LeaveRequest.objects.exclude(status='PENDING').order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
        'title': 'Gestion des demandes '
    }
    return render(request, 'intranet/manage_leave_requests.html', context)


@hr_required
def process_leave_request(request, request_id):
    leave_request = get_object_or_404(LeaveRequest, pk=request_id)
    
    if request.method == 'POST':
        form = LeaveRequestHRForm(request.POST, instance=leave_request)
        if form.is_valid():
            form.save()
            # Logique pour l'envoi d'e-mail ou de message au demandeur (à implémenter plus tard)
            messages.success(request, "La demande de congé a été traitée avec succès.")
            return redirect('manage_leave_requests')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = LeaveRequestHRForm(instance=leave_request)
    
    context = {
        'form': form,
        'leave_request': leave_request,
        'title': 'Traiter une demande de congé'
    }
    return render(request, 'intranet/process_leave_request.html', context)

@login_required
def my_leave_requests(request):
    """
    Affiche la liste des demandes de congé de l'employé connecté.
    """
    my_requests = LeaveRequest.objects.filter(employee=request.user).order_by('-created_at')
    
    context = {
        'my_requests': my_requests,
        'title': 'Mes demandes de congé'
    }
    return render(request, 'intranet/my_leave_requests.html', context)


@login_required
def request_document_view(request):
    if request.method == 'POST':
        form = DocumentRequestForm(request.POST)
        if form.is_valid():
            document_request = form.save(commit=False)
            document_request.employee = request.user
            document_request.save()
            messages.success(request, "Votre demande de document a été soumise avec succès.")
            return redirect('home_view')
    else:
        form = DocumentRequestForm()

    context = {
        'form': form,
    }
    return render(request, 'intranet/request_document.html', context)

@hr_required
def manage_document_requests(request):
    pending_requests = DocumentRequest.objects.filter(status='PENDING').order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'intranet/manage_document_requests.html', context)


@hr_required
def approve_reject_document_request(request, request_id, action):
    document_request = get_object_or_404(DocumentRequest, id=request_id)

    if action == 'approve':
        # On s'assure que la demande est en attente avant de l'approuver
        if document_request.status == 'PENDING':
            # Contexte pour le gabarit HTML du PDF
            context = {
                'employee': document_request.employee,
                'document_type': document_request.document_type.name,
                'generated_date': datetime.date.today(),
            }
            
            # Nom du gabarit à utiliser (stocké dans le modèle DocumentType)
            template_name = document_request.document_type.template_name
            
            # Rendu du gabarit HTML en chaîne de caractères
            html_string = render_to_string(template_name, context)

            # Chemin de sauvegarde du PDF
            filename = f"document_request_{document_request.id}.pdf"
            file_path = os.path.join(settings.MEDIA_ROOT, 'documents', filename)

            # Génération du PDF
            pdf_file = HTML(string=html_string).write_pdf()

            # Sauvegarde du PDF dans le modèle
            document_request.document_file.save(filename, ContentFile(pdf_file), save=True)
            document_request.status = 'GENERATED'
            messages.success(request, f"La demande de {document_request.employee.get_full_name()} a été approuvée et le document a été généré.")
        else:
            messages.info(request, "Cette demande a déjà été traitée.")

    elif action == 'reject':
        if document_request.status == 'PENDING':
            document_request.status = 'REJECTED'
            document_request.rejection_comment = "Demande rejetée par les RH." # Optionnel, peut être amélioré
            messages.warning(request, f"La demande de {document_request.employee.get_full_name()} a été rejetée.")
        else:
            messages.info(request, "Cette demande a déjà été traitée.")

    document_request.save()
    return redirect('manage_document_requests')

@login_required
def download_document_view(request, request_id):
    document_request = get_object_or_404(DocumentRequest, id=request_id)

    # L'utilisateur ne peut télécharger que son propre document
    if document_request.employee != request.user:
        messages.error(request, "Vous n'avez pas la permission de télécharger ce document.")
        return redirect('my_requests_view') # Redirection vers la liste des demandes de l'employé

    # On vérifie si le document est prêt et n'a pas déjà été téléchargé
    if document_request.status == 'GENERATED':
        document_request.status = 'DOWNLOADED'
        document_request.save()
        
        file_path = document_request.document_file.path
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
    elif document_request.status == 'DOWNLOADED':
        messages.warning(request, "Ce document a déjà été téléchargé et n'est plus disponible.")
        return redirect('my_requests_view')
    else:
        messages.info(request, "Votre document n'est pas encore prêt ou a été rejeté.")
        return redirect('my_requests_view')
    

@login_required
def my_document_requests(request):
    document_requests = DocumentRequest.objects.filter(employee=request.user).order_by('-created_at')
    context = {
        'document_requests': document_requests,
    }
    return render(request, 'intranet/my_document_requests.html', context)


@login_required
def project_list_view(request):
    """
    Affiche la liste des projets en fonction du rôle de l'utilisateur.
    - Le Country Manager voit tous les projets.
    - Le Coordinateur de Projet voit uniquement les projets qui lui sont assignés ou où il est membre d'équipe.
    """
    if request.user.groups.filter(name='Country Manager').exists():
        projects = Project.objects.all().order_by('-created_at')
    elif request.user.groups.filter(name='Coordinateur de Projet').exists():
        projects = Project.objects.filter(
            Q(coordinator=request.user) | Q(team_members=request.user)
        ).distinct().order_by('-created_at')
    else:
        # Pour les autres utilisateurs, ne rien afficher
        projects = Project.objects.none()

    context = {
        'projects': projects,
        'is_country_manager': request.user.groups.filter(name='Country Manager').exists(),
        'is_coordinator': request.user.groups.filter(name='Coordinateur de Projet').exists(),
    }
    return render(request, 'intranet/project_list.html', context)


def is_coordinator_of(user, project):
    return user.is_authenticated and user == project.coordinator or user.groups.filter(name='Coordinateurs de Projets').exists()

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Vérification des permissions
    # L'utilisateur doit être le coordinateur ou un membre de l'équipe
    if not (request.user == project.coordinator or request.user in project.team_members.all()):
        raise PermissionDenied("Vous n'avez pas la permission de voir ce projet.")
    
    # Récupérer tous les sites liés à ce projet
    sites = project.sites.all().order_by('name')
    
    context = {
        'project': project,
        'sites': sites,
    }
    return render(request, 'intranet/project_detail.html', context)


@login_required
def site_detail(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    
    # Vérification des permissions
    # L'utilisateur doit être le coordinateur ou un membre de l'équipe du projet parent
    project = site.project
    if not (request.user == project.coordinator or request.user in project.team_members.all()):
        raise PermissionDenied("Vous n'avez pas la permission de voir ce site.")
        
    # Récupérer toutes les tâches liées à ce site
    tasks = site.tasks.all().order_by('due_date')

    context = {
        'site': site,
        'project': project, # Utile pour le lien de retour
        'tasks': tasks,
    }
    return render(request, 'intranet/site_detail.html', context)


@login_required
@country_manager_required
def create_project(request):
    """
    Vue pour créer un nouveau projet. Accessible uniquement par les Country Managers.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.country_manager = request.user # Assigne le projet au Country Manager connecté
            project.save()
            messages.success(request, 'Le projet a été créé avec succès!')
            return redirect('project_dashboard')
    else:
        form = ProjectForm()
    
    return render(request, 'intranet/create_project.html', {'form': form})

@login_required
def add_site(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Vérification des permissions : seul le coordinateur du projet peut ajouter des sites
    if not request.user == project.coordinator:
        raise PermissionDenied("Vous n'avez pas la permission d'ajouter un site à ce projet.")
        
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.project = project
            site.save()
            messages.success(request, f"Le site '{site.name}' a été ajouté au projet.")
            return redirect('project_detail', project_id=project.id)
    else:
        form = SiteForm()

    context = {
        'form': form,
        'project': project,
    }
    return render(request, 'intranet/add_site.html', context)

@login_required
def add_task(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    project = site.project

    # Vérification des permissions : seul le coordinateur du projet peut ajouter des tâches
    if not request.user == project.coordinator:
        raise PermissionDenied("Vous n'avez pas la permission d'ajouter une tâche à ce site.")
        
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.site = site
            task.save()
            messages.success(request, f"L'activité '{task.title}' a été ajoutée avec succès.")
            return redirect('site_detail', site_id=site.id)
    else:
        form = TaskForm()

    context = {
        'form': form,
        'site': site,
        'project': project,
    }
    return render(request, 'intranet/add_task.html', context)

@login_required
def view_rejected_update(request, update_id):
    """Permet à l'employé de voir les détails d'un rejet"""
    update = get_object_or_404(ProfileUpdate, id=update_id, user=request.user, status='rejected')
    
    # Préparer les données pour l'affichage
    rejected_fields = []
    for field_name, comment in update.rejection_comments.items():
        try:
            field = User._meta.get_field(field_name)
            verbose_name = field.verbose_name.title()
        except:
            verbose_name = field_name.replace('_', ' ').title()
        
        rejected_fields.append({
            'name': verbose_name,
            'comment': comment,
            'proposed_value': update.updated_fields.get(field_name, 'N/A')
        })
    
    context = {
        'update': update,
        'rejected_fields': rejected_fields,
    }
    return render(request, 'intranet/view_rejected_update.html', context)

def my_profile_updates(request):
    """
    Affiche l'historique des demandes de mise à jour de l'employé connecté
    """
    updates = ProfileUpdate.objects.filter(user=request.user).order_by('-submitted_at')
    
    context = {
        'updates': updates,
        'title': 'Mes demandes de mise à jour'
    }
    return render(request, 'intranet/my_profile_updates.html', context)

@login_required
def project_list(request):
    """
    Affiche une liste de tous les projets en fonction du rôle de l'utilisateur.
    """
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'intranet/project_list.html', {'projects': projects})

@login_required
def site_list_view(request):
    """
    Affiche la liste des sites en fonction du rôle de l'utilisateur.
    """
    user = request.user
    sites = Site.objects.none()

    if user.groups.filter(name='Country Manager').exists():
        
        # Un Country Manager voit tous les sites des projets de son pays
        if user.country:
            # Cette requête est maintenant valide car le modèle Project a un champ country
            sites = Site.objects.filter(project__country=user.country).order_by('name')
        else:
            # Gérer le cas où le manager n'a pas de pays associé
            sites = Site.objects.none()

    elif user.groups.filter(name='Coordinateur de Projet').exists():
        user_projects = Project.objects.filter(Q(coordinator=user) | Q(team_members=user)).distinct()
        sites = Site.objects.filter(project__in=user_projects).order_by('name')

    context = {
        'sites': sites,
    }
    return render(request, 'intranet/site_list.html', context)