from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/login/', views.api_login_view, name='api_login'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('manage-workers/', views.manage_workers_view, name='manage_workers'),
    path('edit-worker/<int:worker_id>/', views.edit_worker_view, name='edit_worker'),
]
