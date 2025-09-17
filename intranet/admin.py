# intranet/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PayPeriod, Payslip
from .models import LeaveType # Importez le modèle LeaveType
from .models import Notification
from .models import Project, Site, Task
from django.http import HttpResponse
import csv
from .models import *
from .models import Project, Site, Task
from .models import (
    User, Document, Post, JobRole, Department, ProfileUpdate,
    PieceType, ContractType, BankInfo, DocumentType, 
    BadgeDefinition,
    EmployeeBadge,
    Country,
)

from .site_choices import (
    Phase, Batch, RadioType, AntennaType, EnclosureType,
    BBML, ProjectScope, SiteStatus, QAStatus
)

# Enregistrement des modèles de listes déroulantes
@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(PieceType)
class PieceTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(BankInfo)
class BankInfoAdmin(admin.ModelAdmin):
    list_display = ['name']
    
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

# Enregistrement du modèle Country
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    search_fields = ['name', 'code']
    list_filter = ['is_active']


# Enregistrement du modèle User personnalisé
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 
                   'departement', 'job_role', 'country', 'years_of_service')
    list_filter = ('is_active', 'departement', 'job_role', 'country', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    readonly_fields = ('years_of_service', 'date_joined', 'last_login')
    filter_horizontal = ('managed_countries', 'groups', 'user_permissions')
    
    actions = ['activate_users', 'deactivate_users', 'export_users_csv']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateurs activés avec succès.")
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateurs désactivés avec succès.")
    
    def export_users_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employees_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nom', 'Prénom', 'Email', 'Département', 'Poste', 'Statut'])
        
        for user in queryset:
            writer.writerow([
                user.last_name,
                user.first_name,
                user.email,
                user.departement.name if user.departement else '',
                user.job_role.name if user.job_role else '',
                'Actif' if user.is_active else 'Inactif'
            ])
        
        return response
    
    activate_users.short_description = "Activer les utilisateurs sélectionnés"
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"
    export_users_csv.short_description = "Exporter les utilisateurs en CSV"
# Classe d'administration pour ProfileUpdate
@admin.register(ProfileUpdate)
class ProfileUpdateAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'submitted_at', 'job_role', 'departement')
    list_filter = ('status', 'submitted_at', 'job_role', 'departement')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    readonly_fields = [
        'user', 'date_de_naissance', 'nationalite', 'pays_de_naissance', 
        'type_sanguin', 'adresse', 'telephone_personnel', 'piece_type', 
        'piece_number', 'personal_email', 'emergency_contact_name', 
        'emergency_contact_phone', 'allergies', 'maladies_chroniques', 
        'medicaments', 'date_embauche', 'job_role', 'departement', 
        'professional_email', 'contract_type', 'isignum', 'eritop_id', 
        'bank_info', 'bank_account_number', 'cnss', 'dependants', 
        'status', 'submitted_at', 'approved_at', 'rejection_reason'
    ]

# Enregistrement des autres modèles
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'employe', 'document_type', 'date_telechargement')
    list_filter = ('document_type', 'date_telechargement')
    search_fields = ('nom', 'employe__username')

# Enregistrement des nouveaux modèles
@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon', 'color')
    search_fields = ('name',)

@admin.register(EmployeeBadge)
class EmployeeBadgeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'badge', 'awarded_at')
    list_filter = ('badge', 'awarded_at')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name', 'badge__name')
    
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('title', 'content')

@admin.register(PayPeriod)
class PayPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'pay_period', 'gross_salary', 'net_salary', 'created_at')
    list_filter = ('pay_period', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'pay_period__name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications marquées comme lues.")
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications marquées comme non lues.")

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'location', 'created_by')
    list_filter = ('event_type', 'start_date')
    search_fields = ('title', 'description', 'location')
    filter_horizontal = ('participants',)
    date_hierarchy = 'start_date'


# Inline pour les activités (tâches)
class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('title', 'assigned_to', 'due_date', 'status')
    # Permet de modifier le site en un seul clic
    show_change_link = True 

# Inline pour les sites
class SiteInline(admin.TabularInline):
    model = Site
    extra = 1
    fields = ('name', 'location', 'site_id')
    # Permet de modifier le site en un seul clic
    show_change_link = True

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'coordinator', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'coordinator', 'start_date')
    search_fields = ('name', 'description')
    date_hierarchy = 'start_date'
    filter_horizontal = ('team_members',)
    inlines = [SiteInline]

# Enregistrement du modèle Site pour pouvoir y accéder et gérer les tâches
@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'project', 'team_lead', 'location', 'site_id',
        'phase', 'batch', 'installation', 'integration', 'atp'
    )
    list_filter = ('project', 'team_lead', 'phase', 'batch')
    search_fields = ('name', 'site_id', 'location')
    inlines = [TaskInline]
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('project', 'name', 'team_lead', 'location', 'site_id', 'site_area', 'comment')
        }),
        ('Détails du Projet', {
            'fields': ('phase', 'batch', 'project_scope', 'radio_type', 'antenna_type', 'enclosure_type', 'bb_ml')
        }),
        ('Statut et Avancement', {
            'fields': ('installation', 'integration', 'srs', 'imk', 'ehs_1', 'ehs_2', 'qa', 'qa_status', 'atp')
        }),
    )
    
# Enregistrement du modèle Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'site', 'assigned_to', 'due_date', 'status')
    list_filter = ('status', 'assigned_to', 'site__project')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_date'
    
    actions = ['export_tasks_csv']  # Ajout de l'action
    
    def export_tasks_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['Titre', 'Site', 'Projet', 'Assigné à', 'Statut', 'Date d’échéance'])
        for task in queryset:
            writer.writerow([
                task.title,
                task.site.name,
                task.site.project.name,
                task.assigned_to.get_full_name() if task.assigned_to else 'Non assigné',
                task.status,
                task.due_date
            ])
        return response
    export_tasks_csv.short_description = "Exporter les tâches sélectionnées en CSV"


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(RadioType)
class RadioTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(AntennaType)
class AntennaTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(EnclosureType)
class EnclosureTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(BBML)
class BBMLAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(ProjectScope)
class ProjectScopeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(SiteStatus)
class SiteStatusAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(QAStatus)
class QAStatusAdmin(admin.ModelAdmin):
    list_display = ['name']