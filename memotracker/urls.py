from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [

    # All memo list
    path('', views.list_all_memo, name='list_all_memo'),
    # Draft memo list
    path('draft_memo_list/', views.draft_memo_list, name='draft_memo_list'),
    # Approved memo list
    path('approved_memo_list/', views.approved_memo_list, name='approved_memo_list'),
    # Sent memo list
    path('sent_memo_list/', views.sent_memo_list, name='sent_memo_list'),
    # Incoming memo list
    path('incoming_memo_list/', views.incoming_memo_list, name='incoming_memo_list'),
    # outgoing memo list
    path('closed_memo_list/', views.closed_memo_list, name='closed_memo_list'),
    # Outgoing memo list
    path('outgoing_memo_list/', views.outgoing_memo_list, name='outgoing_memo_list'),
    # external memo list
    path('external_memo_list/', views.external_memo_list, name='external_memo_list'),
    # Personal memo list
    path('personal_memo_list/', views.personal_memo_list, name='personal_memo_list'),
    # memo details
    path('memo/<int:pk>', views.memo_detail, name='memo_detail'),
    path('memo/<int:pk>/<str:list_name>', views.memo_detail, name='memo_detail'),
    path('history/', views.memohistory, name='memohistory'),
    path('memotracker/<int:memo_id>/', views.memohistory_detail, name='memohistory_detail'),
    path('history/', views.memohistory, name='memohistory'),
    path('memotracker/<int:memo_id>/', views.memohistory_detail, name='memohistory_detail'),
    path('create_memo/', views.create_memo, name='create_memo'),
    path('external_memo/', views.external_memo, name='external_memo'),
    path('delete_memo/', views.delete_memo, name='delete_memo'),
    path('edit_memo/<int:memo_id>', views.edit_memo, name='edit_memo'),

    path('memo_route/', views.memo_route, name='memo_route'),
    path('memo_route/<int:memo_id>/', views.memo_route, name='memo_route'),
    path('memo_route2/<int:memo_id>/', views.memo_route2, name='memo_route2'),
    path('memo_route_to_all/', views.memo_route_to_all, name='memo_route_to_all'),
    path('memo_route_to_all/<int:memo_id>/', views.memo_route_to_all, name='memo_route_to_all'),
    path('approval_route/', views.approval_route, name='approval_route'),
    path('approval_route/<int:memo_id>/', views.approval_route, name='approval_route'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('approve_memo/', views.approve_memo, name='approve_memo'),
    path('memo_attachment_add/<int:memo_id>', views.memo_attachment_add, name='memo_attachment_add'),
    path('memo_attachments_list/<int:pk>/', views.memo_attachments_list, name='memo_attachments_list'),
    path('memo_attachment_delete/', views.memo_attachment_delete, name='memo_attachment_delete'),
    path('memo_attachment_update/<int:memo_id>/<int:attachment_id>/update/', views.memo_attachment_update, name='memo_attachment_update'),
    path('memo_approval_history/<int:memo_id>', views.memo_approval_history, name='memo_approval_history'),
    path('memo_route_history/<int:memo_id>/<str:list_name>', views.memo_route_history, name='memo_route_history'),
    path('external_memo/', views.external_memo, name='external_memo'),
    path('edit_memo_route/<int:pk>/', views.edit_memo_route, name='edit_memo_route'),
    path('delete_memo_route/<str:list_name>', views.delete_memo_route, name='delete_memo_route'),
    path('reverse_memo_route/<str:list_name>', views.reverse_memo_route, name='reverse_memo_route'),
    path('edit_approval_route/<int:pk>/', views.edit_approval_route, name='edit_approval_route'),
    path('delete_memo_approval/', views.delete_memo_approval, name='delete_memo_approval'),
    path('update_attached_memos/', views.update_attached_memos, name='update_attached_memos'),
    path('count_unread_memos/', views.count_unread_memos, name='count_unread_memos'),
    path('count_unread_memos/<str:listName>', views.count_unread_memos, name='count_unread_memos'),
    path('report/<int:memo_id>/<str:format>/', views.generate_report, name='generate_report'),
    # path('download/report/<int:memo_id>/', views.download_report, name='download_report'),
    path('api/memo/<int:pk>/', views.memo_detail_api, name='memo_detail_api'),
    path('show_notifications/', views.show_notifications, name='show_notifications'),

    ]
