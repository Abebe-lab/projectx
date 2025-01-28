from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.db.models import F, ExpressionWrapper, DurationField
from django.utils import timezone
from .models import Notification, NotificationRecipient


@login_required
def notifications_view(request):
    notifications = NotificationRecipient.objects.annotate(notification_name=F('notification__notification_type__name')).annotate(
        message=F('notification__message')).annotate(url=F('notification__url')).annotate(
        time_difference=ExpressionWrapper(timezone.now() - F('notification__created_date'), output_field=DurationField())).values(
        "id", "message", "url", "notification_name", "time_difference").filter(recipient=request.user, status='unread')
    data = json.dumps(list(notifications), cls=Notification.TimedeltaEncoder)
    return JsonResponse({'message': 'success', 'notifications': data})


@login_required
def change_all_status(request, user_id):
    notifications = NotificationRecipient.objects.filter(recipient=user_id)
    for notify in notifications:
        delete_notification(notify)
    return JsonResponse({'message': 'success'})


def delete_notification(notification_recipient):
    notify_id = notification_recipient.id
    notification_id = notification_recipient.notification_id
    other_recipients = NotificationRecipient.objects.filter(notification_id=notification_id).exclude(id=notify_id)
    notification_recipient.delete()
    if not other_recipients:
        notification = Notification.objects.filter(id=notification_id)
        notification.delete()

@login_required
def change_status(request, notification_id):
    recipient = NotificationRecipient.objects.filter(pk=notification_id)
    if recipient.exists():
        delete_notification(recipient[0])
    return JsonResponse({'message': 'success'})
