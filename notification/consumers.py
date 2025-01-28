import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.first_name = re.sub(r'[^\w\s]', '', self.user.first_name.replace(" ", ""))
        self.last_name = re.sub(r'[^\w\s]', '', self.user.last_name.replace(" ", ""))
        self.GROUP_NAME = "notify_%s_%s_%s" % (self.user.id, self.first_name, self.last_name)

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({'notification': event['notification']}))
