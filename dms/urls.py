from django.urls import path, include
from . import views
from .views import send_memo_to_dms

urlpatterns = [
    path('', views.index, name='index'),
    path('document/create/', views.document_create, name='document_create'),
    path('document/<int:pk>/details/', views.document_details, name='document_details'),
    path('document/<int:pk>/update/', views.document_update, name='document_update'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('search/', views.search_results, name='search'),
    path('dms/document/<int:document_id>/share/', views.share_document, name='share_document'),
    path('send_memo/<int:memo_id>/', send_memo_to_dms, name='send_memo_to_dms'),
    path('list_in_dms/', views.list_in_dms, name='list_in_dms'),

]