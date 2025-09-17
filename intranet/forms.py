from django import forms
from django.contrib.auth import get_user_model
import uuid
import string
import random
from .models import Payslip, PayPeriod
from .models import LeaveType, LeaveRequest
from django.contrib.auth.models import Group 
from .models import DocumentRequest, DocumentType
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, Fieldset
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import ProfileUpdate, Department, JobRole, PieceType, ContractType, BankInfo, Document, DocumentType, Country
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import Project, Site, Task 
from .models import TaskReport
from .constants import TEAM_LEAD_GROUP_NAME 


from .models import Project, Site, Task  # Assurez-vous d'importer les nouveaux modèles


User = get_user_model()

# Formulaire d'enregistrement simplifié pour les administrateurs/RH
class SimplifiedEmployeeRegistrationForm(forms.ModelForm):
    temp_password = None

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'departement', 'job_role', 'country', 'managed_countries', 'is_active']
        widgets = {
            'managed_countries': FilteredSelectMultiple("Pays gérés", is_stacked=False),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('first_name', css_class='form-control-lg'), css_class="col-md-6"),
                Div(Field('last_name', css_class='form-control-lg'), css_class="col-md-6"),
                css_class="row"
            ),
            'email',
            Div(
                Div('departement', css_class="col-md-6"),
                Div('job_role', css_class="col-md-6"),
                css_class="row"
            ),
            'country',
            'managed_countries',
            'is_active',
            Submit('submit', 'Enregistrer l\'employé', css_class='btn-primary mt-4')
        )
        self.fields['departement'].queryset = Department.objects.all()
        self.fields['job_role'].queryset = JobRole.objects.all()
        self.fields['country'].queryset = Country.objects.all()
        self.fields['managed_countries'].queryset = Country.objects.all()
        self.fields['country'].required = False
        self.fields['managed_countries'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        # Ne génère un nouveau username que si l'instance est nouvelle
        if not user.pk:  # Si c'est une création (pas de PK existant)
            base_username = f"{user.first_name.lower()}.{user.last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
            user.employee_id = str(uuid.uuid4())[:8].upper()
            chars = string.ascii_letters + string.digits
            self.temp_password = ''.join(random.choice(chars) for _ in range(12))
            user.set_password(self.temp_password)
        if commit:
            user.save()
        return user
        
# Formulaire pour la soumission des mises à jour de profil par l'utilisateur
class ProfileUpdateForm(forms.ModelForm):
    # DÉFINITION DES CHOIX DE GROUPES SANGUINS
    TYPE_SANGUIN_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    # DÉFINITION DES CHAMPS DE FORMULAIRE PERSONNALISÉS
    # Utilisez ChoiceField pour les groupes sanguins
    type_sanguin = forms.ChoiceField(
        choices=TYPE_SANGUIN_CHOICES,
        required=False,
        label="Type sanguin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Utilisez ModelChoiceField avec un widget de sélection standard
    nationalite = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="Nationalité"
    )
    pays_de_naissance = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="Pays de naissance"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'date_de_naissance', 'nationalite', 
            'pays_de_naissance', 'type_sanguin', 'adresse', 'telephone_personnel', 
            'piece_type', 'piece_number', 'personal_email', 'emergency_contact_name', 
            'emergency_contact_phone', 'allergies', 'maladies_chroniques', 'medicaments', 
            'date_embauche', 'job_role', 'departement', 'professional_email', 
            'contract_type', 'isignum', 'eritop_id', 'bank_info', 'bank_account_number', 
            'cnss', 'dependants', 'photo_profil',
        ]
        
        widgets = {
            'date_de_naissance': forms.DateInput(attrs={'type': 'date'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_telephone_personnel(self):
        telephone = self.cleaned_data.get('telephone_personnel')
        if telephone and not telephone.isdigit():
            raise forms.ValidationError("Le numéro de téléphone ne doit contenir que des chiffres.")
        return telephone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Informations personnelles',
                Div(
                    Div(Field('first_name', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('last_name', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('email', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('personal_email', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('date_de_naissance', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('nationalite', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('pays_de_naissance', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('type_sanguin', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Field('adresse', css_class='form-control'),
                Div(
                    Div(Field('telephone_personnel', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('piece_type', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Field('piece_number', css_class='form-control'),
                Div(
                    Div(Field('emergency_contact_name', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('emergency_contact_phone', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
            ),
            Fieldset(
                'Photo de profil',
                Field('photo_profil', css_class='form-control'),
            ),
            Fieldset(
                'Informations médicales',
                Field('allergies', css_class='form-control'),
                Field('maladies_chroniques', css_class='form-control'),
                Field('medicaments', css_class='form-control'),
            ),
            Fieldset(
                'Informations professionnelles',
                Div(
                    Div(Field('date_embauche', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('job_role', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('departement', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('professional_email', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('contract_type', css_class='form-control'), css_class="col-md-4"),
                    Div(Field('isignum', css_class='form-control'), css_class="col-md-4"),
                    Div(Field('eritop_id', css_class='form-control'), css_class="col-md-4"),
                    css_class="row"
                ),
            ),
            Fieldset(
                'Informations administratives',
                Div(
                    Div(Field('bank_info', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('bank_account_number', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
                Div(
                    Div(Field('cnss', css_class='form-control'), css_class="col-md-6"),
                    Div(Field('dependants', css_class='form-control'), css_class="col-md-6"),
                    css_class="row"
                ),
            ),
            Submit('submit', 'Soumettre les mises à jour', css_class='btn-primary mt-4')
        )
        # Ajout des requêtes pour les champs de clés étrangères
        self.fields['piece_type'].queryset = PieceType.objects.all()
        self.fields['contract_type'].queryset = ContractType.objects.all()
        self.fields['bank_info'].queryset = BankInfo.objects.all()
        self.fields['job_role'].queryset = JobRole.objects.all()
        self.fields['departement'].queryset = Department.objects.all()


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['nom', 'document_type', 'fichier']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'nom',
            'document_type',
            'fichier',
            Submit('submit', 'Télécharger', css_class='btn-success mt-4')
        )
        self.fields['document_type'].queryset = DocumentType.objects.all()



class PayPeriodForm(forms.ModelForm):
    class Meta:
        model = PayPeriod
        fields = ['name', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PayslipForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = [
            'employee', 'pay_period', 'base_salary', 'gross_salary', 
            'net_salary', 'taxes', 'deductions', 'bonuses', 
            'other_payments'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'pay_period': forms.Select(attrs={'class': 'form-control'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'gross_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'net_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'taxes': forms.NumberInput(attrs={'class': 'form-control'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control'}),
            'bonuses': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_payments': forms.NumberInput(attrs={'class': 'form-control'}),
        }
class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'leave_type': forms.Select(attrs={'class': 'form-control'})
        }

class LeaveRequestHRForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['status', 'rejection_comment']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'rejection_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }



class DocumentRequestForm(forms.ModelForm):
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(),
        label="Type de document",
        empty_label="Sélectionnez un type de document",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = DocumentRequest
        fields = ['document_type', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        labels = {
            'reason': "Raison de la demande",
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # Assurez-vous que 'coordinator' est dans la liste des champs
        fields = ['name', 'country', 'coordinator', 'start_date', 'end_date', 'description', 'team_members']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupère le groupe 'Coordinateur de Projet'
        try:
            coordinator_group = Group.objects.get(name='Coordinateur de Projet')
            # Filtre la liste déroulante pour n'afficher que les utilisateurs de ce groupe
            self.fields['coordinator'].queryset = coordinator_group.user_set.all().order_by('first_name', 'last_name')
        except Group.DoesNotExist:
            # Gère le cas où le groupe n'existe pas pour éviter une erreur
            self.fields['coordinator'].queryset = User.objects.none()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'country',
            'coordinator',
            Div(
                Div('start_date', css_class='col-md-6 mb-3'),
                Div('end_date', css_class='col-md-6 mb-3'),
                css_class='row'
            ),
            'description',
            'team_members',
            Submit('submit', 'Créer le projet', css_class='btn-primary mt-3')
        )

class AddSiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'name', 'team_lead', 'location', 'site_id', 'site_area',
            'phase', 'batch', 'project_scope', 'radio_type', 'antenna_type',
            'enclosure_type', 'bb_ml', 'installation', 'integration', 'srs',
            'imk', 'ehs_1', 'ehs_2', 'qa', 'qa_status', 'atp', 'comment'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            team_lead_group = Group.objects.get(name=TEAM_LEAD_GROUP_NAME)
            self.fields['team_lead'].queryset = User.objects.filter(groups=team_lead_group).order_by('last_name')
        except Group.DoesNotExist:
            self.fields['team_lead'].queryset = User.objects.none()



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'description',
            'assigned_to',
            'due_date',
            'status',
            Submit('submit', 'Ajouter l\'activité', css_class='btn-primary mt-3')

        )

class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']

class TaskReportForm(forms.ModelForm):
    class Meta:
        model = TaskReport
        fields = ['report_text', 'photo']
        widgets = {
            'report_text': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'report_text',
            'photo',
            Submit('submit', 'Ajouter le rapport', css_class='btn-primary mt-3')
        )

