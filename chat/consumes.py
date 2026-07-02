import json
from urllib.parse import parse_qs

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from rest_framework.authtoken.models import Token


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        print("CONNECT START")

        query = parse_qs(self.scope["query_string"].decode())
        token_key = query.get("token", [None])[0]

        print("TOKEN:", token_key)

        try:
            token = Token.objects.get(key=token_key)
            self.user = token.user

            self.room_group_name = "chat_sbk_developer"

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()

            print(f"{self.user.username} Connected")

        except Exception as e:
            print("CONNECT ERROR:", e)
            self.close()

    def disconnect(self, close_code):
        print(f"Disconnected: {close_code}")

        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)

            message = data.get("message", "").strip()

            if not message:
                return

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "message": message,
                }
            )

        except Exception as e:
            print("RECEIVE ERROR:", e)

    def chat_message(self, event):
        try:
            self.send(text_data=json.dumps({
                "user_id": event["user_id"],
                "username": event["username"],
                "message": event["message"],
                "is_sender": self.user.id == event["user_id"]
            }))

        except Exception as e:
            print("SEND ERROR:", e)
