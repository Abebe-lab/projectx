from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_view, name='notification'),
    path('<int:user_id>', views.change_all_status, name='change_all_status'),
    path('open/<int:notification_id>', views.change_status, name='change_status')
]
