from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('technician/dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('technician/create/', views.create_jobcard, name='create_jobcard'),
    path('technician/job/<int:job_id>/', views.technician_job_detail, name='technician_job_detail'),
    
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/review/<int:job_id>/', views.manager_job_review, name='manager_job_review'),
    
    path('manager/settings/', views.manager_settings, name='manager_settings'),
    path('manager/users/', views.manager_user_list, name='manager_user_list'),
    path('manager/users/create/', views.manager_user_create, name='manager_user_create'),
    path('manager/users/edit/<int:user_id>/', views.manager_user_edit, name='manager_user_edit'),
    
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
