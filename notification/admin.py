from django.contrib import admin

from .models import NotificationType, Notification, NotificationRecipient

# Register your models here.
admin.site.register(NotificationType)
admin.site.register(Notification)
admin.site.register(NotificationRecipient)
