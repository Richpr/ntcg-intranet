# intranet/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings 
from django_countries.fields import CountryField
from PIL import Image
import uuid
from django.utils import timezone
from datetime import datetime
from django.db.models import JSONField # L'importation correcte pour SQLite


# Modèles pour les listes déroulantes
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Département")

    def __str__(self):
        return self.name

class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du document")
    description = models.TextField(blank=True, verbose_name="Description")
    template_name = models.CharField(max_length=255, help_text="Nom du fichier de gabarit HTML pour ce document (ex: attestation_travail.html)")
    country_specific = models.BooleanField(default=False, verbose_name="Spécifique à un pays")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Type de document"
        verbose_name_plural = "Types de documents"


class JobRole(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Rôle de l'emploi")

    def __str__(self):
        return self.name
        
class PieceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Type de pièce")

    def __str__(self):
        return self.name

class ContractType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Type de contrat")

    def __str__(self):
        return self.name

class BankInfo(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la banque")

    def __str__(self):
        return self.name
    

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du pays")
    code = models.CharField(max_length=2, unique=True, verbose_name="Code ISO 3166-1 alpha-2")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"


# Extension du modèle User de Django
class User(AbstractUser):
    # Informations personnelles
    date_de_naissance = models.DateField(null=True, blank=True)
    # Utilisez CountryField pour les champs de pays et nationalité
    nationalite = CountryField(blank=True)
    pays_de_naissance = CountryField(blank=True)
    type_sanguin = models.CharField(max_length=5, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone_personnel = models.CharField(max_length=20, blank=True)
    piece_type = models.ForeignKey(PieceType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de pièce d'identité")
    piece_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de la pièce d'identité")
    personal_email = models.EmailField(blank=True, null=True, verbose_name="Email personnel")
    emergency_contact_name = models.CharField(max_length=255, blank=True, verbose_name="Nom et prénom du contact d'urgence")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du contact d'urgence")
    
    # Informations médicales
    allergies = models.TextField(blank=True)
    maladies_chroniques = models.TextField(blank=True)
    medicaments = models.TextField(blank=True)

    # Informations professionnelles
    job_role = models.ForeignKey(JobRole, on_delete=models.SET_NULL, null=True, blank=True)
    departement = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    professional_email = models.EmailField(blank=True, null=True, verbose_name="Email professionnel")
    contract_type = models.ForeignKey(ContractType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de contrat")
    isignum = models.CharField(max_length=100, blank=True, verbose_name="Numéro Isignum")
    eritop_id = models.CharField(max_length=100, blank=True, verbose_name="ID Eritop")
    
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pays de l'employé")
    managed_countries = models.ManyToManyField(Country, related_name='managers', blank=True, verbose_name="Pays gérés")


    # Informations administratives
    bank_info = models.ForeignKey(BankInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nom de la banque")
    bank_account_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro de compte bancaire")
    cnss = models.CharField(max_length=50, verbose_name="Numéro CNSS/Sécurité Sociale", blank=True)
    dependants = models.TextField(blank=True)

    employee_id = models.CharField(max_length=100, unique=True, blank=True, verbose_name="Numéro de matricule")
    photo_profil = models.ImageField(upload_to='photos_profils/', null=True, blank=True)
    

    def save(self, *args, **kwargs):
        # Génération automatique du matricule si ce n'est pas déjà fait
        if not self.employee_id:
            self.employee_id = str(uuid.uuid4())[:8].upper()
            
        super().save(*args, **kwargs) # Sauvegarde de l'instance
        
        # Redimensionnement de la photo après la sauvegarde
        if self.photo_profil:
            img = Image.open(self.photo_profil.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.photo_profil.path)



    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def years_of_service(self):
        if self.date_embauche:
            today = datetime.now().date()
            return today.year - self.date_embauche.year - (
                (today.month, today.day) < (self.date_embauche.month, self.date_embauche.day)
            )
        return 0
    
    def get_pending_updates(self):
        return self.profile_updates.filter(status='pending')
    
    def get_recent_documents(self, days=30):
        return self.documents.filter(
            date_telechargement__gte=datetime.now() - timedelta(days=days)
        )
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['departement']),
            models.Index(fields=['country']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'country']),
        ]





# Modèle Notification
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('success', 'Succès'),
        ('error', 'Erreur'),
    ]
    
    ICON_CHOICES = [
        ('bell', 'bell'),
        ('envelope', 'envelope'),
        ('check-circle', 'check-circle'),
        ('exclamation-triangle', 'exclamation-triangle'),
        ('user', 'user'),
        ('file-alt', 'file-alt'),
        ('calendar-alt', 'calendar-alt'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='bell')
    is_read = models.BooleanField(default=False)
    related_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lien")
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

# Modèle Event
class Event(models.Model):
    EVENT_TYPES = [
        ('meeting', 'Réunion'),
        ('training', 'Formation'),
        ('event', 'Événement'),
        ('holiday', 'Jour férié'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='event')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=100, blank=True)
    participants = models.ManyToManyField(User, blank=True, related_name='events')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%d/%m/%Y')}"
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def duration(self):
        return self.end_date - self.start_date





# Modèle pour les documents de l'employé
class Document(models.Model):
    employe = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    nom = models.CharField(max_length=255)
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de document")
    fichier = models.FileField(upload_to='documents_employes/')
    date_telechargement = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
    def clean(self):
        # Validation de la taille du fichier (max 5MB)
        if self.fichier and self.fichier.size > 5 * 1024 * 1024:
            raise ValidationError("Le fichier ne doit pas dépasser 5MB.")
        
        # Validation du type de fichier
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png']
        if not any(self.fichier.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError("Type de fichier non autorisé.")

# Modèle pour les badges
class BadgeDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du badge")
    description = models.TextField(verbose_name="Description du badge")
    icon = models.CharField(max_length=50, help_text="Nom d'une icône CSS (ex: 'fa-star')", verbose_name="Icône")
    # On peut ajouter un champ pour la couleur du badge si tu le souhaites
    color = models.CharField(max_length=7, default='#007bff', verbose_name="Couleur du badge (code hexa)")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Définition de badge"
        verbose_name_plural = "Définitions de badges"

# Modèle pour l'attribution des badges aux employés
# Il lie un employé à un badge spécifique avec une date d'attribution
class EmployeeBadge(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_badges', verbose_name="Employé")
    badge = models.ForeignKey(BadgeDefinition, on_delete=models.CASCADE, verbose_name="Badge attribué")
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'attribution")
    
    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} a reçu le badge '{self.badge.name}'"
        
    class Meta:
        # Permet de s'assurer qu'un employé ne peut pas recevoir le même badge deux fois
        unique_together = ('employee', 'badge')
        verbose_name = "Badge d'employé"
        verbose_name_plural = "Badges des employés"

# Modèle pour les actualités
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
# Modèle pour les mises à jour de profil en attente
class ProfileUpdate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_updates')
    
    # Champ pour stocker les modifications
    updated_fields = models.JSONField(verbose_name="Champs mis à jour", default=dict)
    
    # Photo de profil
    photo_profil = models.ImageField(upload_to='photos_profils_updates/', null=True, blank=True)
    
    # Informations personnelles
    date_de_naissance = models.DateField(null=True, blank=True)
    nationalite = CountryField(blank=True)  # Utilise CountryField
    pays_de_naissance = CountryField(blank=True)  # Utilise CountryField
    type_sanguin = models.CharField(max_length=5, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone_personnel = models.CharField(max_length=20, blank=True)
    piece_type = models.ForeignKey(PieceType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de pièce d'identité")
    piece_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de la pièce d'identité")
    personal_email = models.EmailField(blank=True, null=True, verbose_name="Email personnel")
    emergency_contact_name = models.CharField(max_length=255, blank=True, verbose_name="Nom et prénom du contact d'urgence")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone du contact d'urgence")
    
    # Informations médicales
    allergies = models.TextField(blank=True)
    maladies_chroniques = models.TextField(blank=True)
    medicaments = models.TextField(blank=True)

    # Informations professionnelles
    job_role = models.ForeignKey(JobRole, on_delete=models.SET_NULL, null=True, blank=True)
    departement = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    professional_email = models.EmailField(blank=True, null=True, verbose_name="Email professionnel")
    contract_type = models.ForeignKey(ContractType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de contrat")
    isignum = models.CharField(max_length=100, blank=True, verbose_name="Numéro Isignum")
    eritop_id = models.CharField(max_length=100, blank=True, verbose_name="ID Eritop")
    
    # Informations administratives
    bank_info = models.ForeignKey(BankInfo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Nom de la banque")
    bank_account_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro de compte bancaire")
    cnss = models.CharField(max_length=50, verbose_name="Numéro CNSS/Sécurité Sociale", blank=True)
    dependants = models.TextField(blank=True)
    
    # Statut et métadonnées
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # UN SEUL champ rejection_comments (supprimez le doublon)
    rejection_comments = models.JSONField(default=dict, blank=True, verbose_name="Commentaires de rejet")
    
    def __str__(self):
        return f"Mise à jour de profil pour {self.user.username} ({self.get_status_display()})"
class PayPeriod(models.Model):
    """
     Modèle pour définir une période de paie.
    Exemple : 'Août 2025'
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la période")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Période active")

    def __str__(self):
        return self.name

class Payslip(models.Model):
    """
    Modèle pour stocker les informations de la fiche de paie d'un employé.
    """
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payslips',
        verbose_name="Employé"
    )
    pay_period = models.ForeignKey(
        PayPeriod,
        on_delete=models.CASCADE,
        related_name='payslips',
        verbose_name="Période de paie"
    )
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire de base")
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire brut")
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salaire net")
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Impôts")
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Déductions")
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Primes et bonus")
    other_payments = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Autres paiements")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        unique_together = ('employee', 'pay_period') # Un employé ne peut avoir qu'une seule fiche de paie par période

    def __str__(self):
        return f"Fiche de paie de {self.employee.get_full_name()} pour {self.pay_period.name}"
    
    

class LeaveType(models.Model):
    """
    Modèle pour définir les différents types de congés.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Type de congé")

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    """
    Modèle pour stocker une demande de congé d'un employé.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Refusée'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name="Employé"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Type de congé"
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    reason = models.TextField(verbose_name="Motif de la demande")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    rejection_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire (si refusé)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de la demande")

    def __str__(self):
        return f"Demande de congé de {self.employee.get_full_name()} du {self.start_date} au {self.end_date}" 


# Modèle pour les demandes de documents
class DocumentRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Rejetée'),
        ('GENERATED', 'Générée'),
        ('DOWNLOADED', 'Téléchargée'),
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='document_requests')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name='requests')
    reason = models.TextField(blank=True, null=True, help_text="Raison de la demande (ex: démarches administratives)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_comment = models.TextField(blank=True, null=True, help_text="Commentaire en cas de refus")
    document_file = models.FileField(upload_to='documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Demande de {self.document_type.name} par {self.employee.get_full_name()}"

    class Meta:
        ordering = ['-created_at']


# Modèle pour les projets globaux
class Project(models.Model):
    STATUS_CHOICES = [
        ('À FAIRE', 'À faire'),
        ('EN COURS', 'En cours'),
        ('TERMINÉ', 'Terminé'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nom du projet")
    description = models.TextField(verbose_name="Description du projet", blank=True, null=True)
    start_date = models.DateField(verbose_name="Date de début", null=True, blank=True)
    end_date = models.DateField(verbose_name="Date de fin estimée", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='À FAIRE', verbose_name="Statut")
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name="Coordinateur du projet"
    )
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        verbose_name="Membres de l'équipe"
    )
    country = CountryField(blank=True, verbose_name="Pays du projet")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"


# Modèle pour les sites de télécommunication
class Site(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom du site")
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name="Projet associé"
    )
    location = models.CharField(max_length=255, verbose_name="Localisation", blank=True, null=True)
    site_id = models.CharField(max_length=50, unique=True, verbose_name="Identifiant unique du site", blank=True, null=True)
    
    # Ajoutez ce nouveau champ
    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_sites',
        verbose_name="Team Lead Assigné"
    )


    def __str__(self):
        return f"{self.name} ({self.project.name})"

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"


    def get_team_leads(self):
        """Retourne tous les Team Leads travaillant sur ce site"""
        return User.objects.filter(
            groups__name='Team Lead',
            tasks__site=self
        ).distinct()
    
    def completed_tasks_count(self):
        """Retourne le nombre de tâches terminées"""
        return self.tasks.filter(status='TERMINÉ').count()
    
    def total_tasks_count(self):
        """Retourne le nombre total de tâches"""
        return self.tasks.count()
    
    def completion_percentage(self):
        """Retourne le pourcentage de completion"""
        total = self.total_tasks_count()
        if total == 0:
            return 0
        return (self.completed_tasks_count() / total) * 100
    
    def get_user_task_count(self, user=None):
        """
        Retourne le nombre de tâches assignées à un utilisateur sur ce site
        """
        if user:
            return self.tasks.filter(assigned_to=user).count()
        return self.tasks.count()
    
    def get_user_tasks(self, user=None):
        """
        Retourne les tâches assignées à un utilisateur sur ce site
        """
        if user:
            return self.tasks.filter(assigned_to=user)
        return self.tasks.all()

# Modèle pour les activités/tâches sur un site
class Task(models.Model):
    STATUS_CHOICES = [
        ('À FAIRE', 'À faire'),
        ('EN COURS', 'En cours'),
        ('TERMINÉ', 'Terminé'),
        ('EN ATTENTE', 'En attente'),
    ]

    title = models.CharField(max_length=255, verbose_name="Titre de l'activité")
    description = models.TextField(verbose_name="Description de l'activité", blank=True, null=True)
    site = models.ForeignKey(
        'Site',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Site associé"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name="Assigné à"
    )
    due_date = models.DateField(verbose_name="Date d'échéance", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='À FAIRE', verbose_name="Statut")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} sur {self.site.name}"

    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"


class TaskReport(models.Model):
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="Tâche associée"
    )
    report_text = models.TextField(verbose_name="Description de l'avancement", blank=True, null=True)
    photo = models.ImageField(upload_to='task_photos/', verbose_name="Photo de l'avancement", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Rapporté par"
    )

    def __str__(self):
        return f"Rapport pour {self.task.title} par {self.reported_by.get_full_name()}"

    class Meta:
        verbose_name = "Rapport de Tâche"
        verbose_name_plural = "Rapports de Tâche"
        ordering = ['-created_at']

class ProjectManager(models.Manager):
    def with_related_data(self):
        return self.get_queryset().select_related(
            'coordinator'
        ).prefetch_related(
            'team_members', 'sites', 'sites__tasks'
        )