import json
from urllib.parse import parse_qs

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from rest_framework.authtoken.models import Token
from .models import ChatRoom,MessageDelivery,Messages


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        print("CONNECT START")

        query = parse_qs(self.scope["query_string"].decode())
        token_key = query.get("token", [None])[0]
        room_id = query.get("room_id", [None])[0]

        print("TOKEN:", token_key)

        try:
            token = Token.objects.get(key=token_key)
            self.user = token.user

            self.room_group_name = ChatRoom.objects.get(id=room_id).name

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()
            
            room = ChatRoom.objects.get(id=room_id)
            pending = MessageDelivery.objects.filter(
            user=self.user,
            delivered=False,
            messages_room=room
            )

            for item in pending:

                self.send(text_data=json.dumps({
                    "user_id": item.message.user.id,
                    "username": item.message.user.username,
                    "message": item.message.content,
                    }))

                item.delivered = True
                item.save()

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
            room_id = data.get("room_id")
            
            room = ChatRoom.objects.get(id=room_id)

            if not message:
                return
            msg = Messages.objects.create(
                user=self.user,
                room=room,
                content=message
                )
            members = room.members.exclude(id=self.user.id)

            for member in members:
                MessageDelivery.objects.create(
                message=msg,
                user=member
                )

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "message": msg.content,
                    "room_id":room.id,
                    "message_id":msg.id
                }
            )

        except Exception as e:
            print("RECEIVE ERROR:", e)

    def chat_message(self, event):
        try:
            
            MessageDelivery.objects.filter(
                message_id=event["message_id"],
                user=self.user
                ).update(delivered=True)
            
            self.send(text_data=json.dumps({
                "user_id": event["user_id"],
                "username": event["username"],
                "message": event["message"],
                "is_sender": self.user.id == event["user_id"],
                "room_id":event["room_id"],
                "message_id":event["message_id"]
            }))

        except Exception as e:
            print("SEND ERROR:", e)
