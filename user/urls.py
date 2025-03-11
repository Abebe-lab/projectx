from .views import CustomPasswordChangeView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView
from .views import CustomResetPasswordView
from .views import forgot_pin, reset_pin


urlpatterns = [
    path('login/', CustomLoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/user/login/'), name='logout'),
    #path('password_change/', auth_views.PasswordChangeView.as_view(template_name='user/password_change.html'), name='password_change'),
    path('password_change/', CustomPasswordChangeView.as_view(template_name='user/password_change.html'), name='password_change'),
    path('password_change/done/', views.password_change_done, name='password_change_done'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('dashboard_config/', views.dashboard_config, name='dashboard_config'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('password_reset/', CustomResetPasswordView.as_view(), name='password_reset'),
    path('accept_pin/', views.accept_pin, name='accept_pin'),
    path('forgot_pin/', views.forgot_pin, name='forgot_pin'),
    path('reset_pin/<str:username>/', views.reset_pin, name='reset_pin'),

    # Other URL patterns
]
