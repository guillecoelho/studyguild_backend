import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


class ReunionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.reunion_id = self.scope["url_route"]["kwargs"]["reunion_id"]
        self.group_name = f"reunion_{self.reunion_id}"

        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if not token_list:
            await self.close(code=4001)
            return

        try:
            AccessToken(token_list[0])
        except (InvalidToken, TokenError):
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def reunion_message(self, event):
        await self.send(text_data=json.dumps({
            "event": "message_created",
            "message": event["message"],
        }))
