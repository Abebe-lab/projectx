from django.urls import path
from . import views

urlpatterns = [
    path('customer/', views.get_all_customers, name='customer'),
    path('search_customer/', views.search_customer, name='search_customer'),
    path('add_customer/', views.add_customer, name='add_customer'),
    path('add_new_customer/', views.add_new_customer, name='add_new_customer'),
    path('add_new_customer/<str:caller>', views.add_new_customer, name='add_new_customer'),
    path('edit_customer/<int:pk>', views.edit_customer, name='edit_customer'),
    path('delete_customer/', views.delete_customer, name='delete_customer'),
    path('get_bu_users/<int:bu_id>', views.get_bu_users, name='get_bu_users'),
    path('get_business_units/', views.get_business_units, name='get_business_units'),
    path('get_external_customers/', views.get_external_customers, name='get_external_customers'),
    # path('get_personal_users/', views.get_personal_users, name='get_personal_users'),
]
