from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import NotificationRecipient

from firebase_admin.messaging import Message
from fcm_django.models import FCMDevice
from firebase_admin import messaging, exceptions


@receiver(post_save, sender=NotificationRecipient)
def notification_created(sender, instance, created, **kwargs):
    if created:
        notification = instance.get_notification_recipient()
        channel_layer = get_channel_layer()
        group_name = "notify_%s" % notification['recipient_name']
        event = {
            'type': 'send_notification',
            'notification': notification
        }
        async_to_sync(channel_layer.group_send)(
            group_name, event
        )

        devices = FCMDevice.objects.filter(user_id=notification['recipient_id'])
        if devices.exists():
            message_obj = Message(
                data={
                    'title': notification['notification_name'],
                    'body': notification['message'],
                    'url': notification['url'],
                    'icon_url': '../static/img/Memo.png'
                },
                token=devices.first().registration_id
            )
            print(message_obj)
            try:
                messaging.send(message_obj)
            except exceptions.FirebaseError as e:
                error_code = e.code
                error_message = str(e)
                print('FCM messaging error: ', error_code, error_message)
            except Exception as e:
                print('Error occurred: ', str(e))
