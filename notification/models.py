from django.db import models
from django.contrib.auth.models import User
from django.db.models import F, ExpressionWrapper, DurationField, Value, CharField, Func
from django.db.models.functions import Cast
from django.db.models.expressions import RawSQL
from django.utils import timezone
from json import JSONEncoder
from datetime import timedelta


class NotificationType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Notification(models.Model):
    notification_type = models.ForeignKey(NotificationType, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=200, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.message

    @classmethod
    def create_notification(cls, sender, notification_type, message, url):
        instance = cls(notification_type=notification_type, message=message, url=url, created_by=sender)
        instance.save()
        return instance

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_date']

    class TimedeltaEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, timedelta):
                minutes = obj.seconds // 60
                hours = minutes // 60
                remaining_minutes = minutes % 60
                return {
                    'days': obj.days,
                    'hours': hours,
                    'minutes': remaining_minutes
                }
            return super().default(obj)

    def get_notification(self):
        notification = Notification.objects.filter(pk=self.pk).annotate(notification_name=F('notification_type__name'),
                                                                        recipient_name=Func(F('recipient__id'), Value('_'),
                                                                                            F('recipient__first_name'), Value('_'),
                                                                                            F('recipient__last_name'), function='CONCAT', output_field=CharField())).annotate(
            time_difference=ExpressionWrapper(timezone.now() - F('created_date'), output_field=DurationField())).values(
            "id", "recipient_name", "message", "notification_name", "time_difference")
        for obj in notification:
            time_difference = obj['time_difference']
            formatted_time_difference = Notification.TimedeltaEncoder().default(time_difference)
            obj['time_difference'] = formatted_time_difference
        return notification.first()


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notify_to')
    status = models.CharField(choices=[
        ('unread', 'Unread'),
        ('read', 'Read')
    ], default='unread')

    def __str__(self):
        return self.notification.message + " To " + self.recipient.first_name + " " + self.recipient.last_name

    class Meta:
        ordering = ['-notification__created_date']

    @classmethod
    def create_notification_recipient(cls, recipient, notification):
        instance = cls(recipient=recipient, notification=notification)
        instance.save()
        return instance

    def get_notification_recipient(self):
        recipient_name = RawSQL(
            r"LEFT(REGEXP_REPLACE(CONCAT_WS('_', TRIM(BOTH ' ' FROM %s), TRIM(BOTH ' ' FROM %s), TRIM(BOTH ' ' FROM %s)), '[^A-Za-z0-9_\-.]', '', 'g'), 100)",
            (str(self.recipient_id), self.recipient.first_name, self.recipient.last_name)
        )
        notification_recipient = NotificationRecipient.objects.filter(pk=self.pk).annotate(notification_name=F('notification__notification_type__name'),
                                                                                           recipient_name=recipient_name).annotate(
            time_difference=ExpressionWrapper(timezone.now() - F('notification__created_date'), output_field=DurationField())).annotate(
            message=F('notification__message')).annotate(url=F('notification__url')).values(
            'id', 'recipient_id', 'recipient_name', 'message', 'url', 'notification_name', 'time_difference')
        for obj in notification_recipient:
            time_difference = obj['time_difference']
            formatted_time_difference = Notification.TimedeltaEncoder().default(time_difference)
            obj['time_difference'] = formatted_time_difference
        return notification_recipient[0]