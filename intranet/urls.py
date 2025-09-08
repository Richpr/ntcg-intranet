from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # URL pour le tableau de bord principal
    path('', views.home_view, name='home_view'),

    # URLs pour les notifications et les statistiques
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/statistics/', views.api_statistics, name='api_statistics'),

    # URLs pour la gestion des RH
    # Ajoute au début des urlpatterns
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/bank-info/', views.employee_bank_info, name='employee_bank_info'),
    
    # URLs pour les demandes de documents
    path('document-requests/', views.manage_document_requests, name='manage_document_requests'),
    path('document-requests/manage/<int:request_id>/<str:action>/', views.approve_reject_document_request, name='approve_reject_document_request'),
    path('my-documents/', views.my_document_requests, name='my_document_requests'),
    path('document-request/', views.request_document_view, name='request_document'),
    path('document-request/download/<int:request_id>/', views.download_document_view, name='download_document'),

    # URLs pour les profils des employés
    path('profile/', views.profile_view, name='my_profile'),
    path('profile/<int:user_id>/', views.profile_view, name='user_profile'),
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('profile/<int:user_id>/safety_passport/', views.safety_passport_view, name='safety_passport'),
    
    # URLs pour la gestion des employés
    path('register/employee/', views.register_employee, name='register_employee'),
    path('employees/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    path('employees/', views.employee_directory, name='employee_directory'),

    # URLs pour la connexion et la déconnexion
    path('login/', auth_views.LoginView.as_view(template_name='intranet/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # URLs pour le workflow d'approbation
    path('updates/pending/', views.pending_updates_list, name='pending_updates_list'),
    path('updates/review/<int:update_id>/', views.review_profile_update, name='review_profile_update'),
    path('updates/approve/<int:update_id>/', views.approve_update, name='approve_update'),
    path('updates/reject/<int:update_id>/', views.reject_update, name='reject_update'),
    path('updates/rejected/<int:update_id>/', views.view_rejected_update, name='view_rejected_update'),
    path('my-profile-updates/', views.my_profile_updates, name='my_profile_updates'),

    # URLs pour la gestion des paies
    path('payslips/', views.payslip_list, name='payslip_list'),
    path('payslips/create/', views.create_payslip, name='create_payslip'),
    path('payslips/edit/<int:payslip_id>/', views.edit_payslip, name='edit_payslip'),

    # URLs pour les demandes de congés
    path('leave-request/submit/', views.submit_leave_request, name='submit_leave_request'),
    path('leave-request/mine/', views.my_leave_requests, name='my_leave_requests'),
    path('hr/leave-requests/', views.manage_leave_requests, name='manage_leave_requests'),
    path('hr/leave-requests/<int:request_id>/process/', views.process_leave_request, name='process_leave_request'),

    # URLs pour la gestion des projets et sites
    path('projects/', views.project_list, name='project_dashboard'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/add-site/', views.add_site, name='add_site'),
    path('sites/', views.site_list_view, name='site_list'),
    path('sites/<int:site_id>/', views.site_detail, name='site_detail'),
    path('sites/<int:site_id>/add-task/', views.add_task, name='add_task'),
]

# Cette ligne est CRUCIALE pour le développement !
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)