from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin
    path('admin/', views.admin_panel, name='admin_panel'),
    
    # User
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # API (for AJAX/polling)
    path('api/task/<str:task_id>/status/', views.api_task_status, name='api_task_status'),
]