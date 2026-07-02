import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync # গ্রুপ সেন্ডের জন্য এটি প্রয়োজন
from .models import Messages, ChatRoom
from urllib.parse import parse_qs
from rest_framework.authtoken.models import Token

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print("CONNECT START")

        query = parse_qs(self.scope["query_string"].decode())
        token_key = query.get("token", [None])[0]
        print(token_key)

        try:
            token = Token.objects.get(key=token_key)
            print("TOKEN OK")

            self.user = token.user

            self.room_group_name = "chat_sbk_developer"

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            print("GROUP OK")

            self.accept()

            print("ACCEPT OK")

        except Exception as e:
            print("ERROR:", e)
            self.close()

    def disconnect(self, close_code):
        # কানেকশন বন্ধ হলে গ্রুপ থেকে বের করে দেওয়া
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def receive(self, text_data=None):
        data = json.loads(text_data)
        room = ChatRoom.objects.get(name="SBK Developer")
        
        # ডাটাবেজে মেসেজ সেভ করা
        msg = Messages.objects.create(
            room=room,
            user=self.user,
            content=data["message"]
        )
        
        # গ্রুপের সবার কাছে মেসেজটি ব্রডকাস্ট (Broadcast) করা
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message', # নিচের মেথডটিকে কল করবে
                'user_id': msg.user.id,
                'username': msg.user.username,
                'message': msg.content,
                'uploaded_at': msg.uploaded_at.isoformat()
            }
        )

    # গ্রুপ থেকে মেসেজ রিসিভ করে ফ্রন্টএন্ডে পাঠানো
    def chat_message(self, event):
        # চেক করা: এই মেসেজটি যে ইউজার রিসিভ করছে, সে নিজেই কি প্রেরক?
        is_sender = (self.user.id == event['user_id'])
        
        self.send(text_data=json.dumps({
            "user_id": event['user_id'],
            "username": event['username'],
            "message": event['message'],
            "uploaded_at": event['uploaded_at'],
            "is_sender": is_sender # ফ্রন্টএন্ডের জন্য নতুন ফ্ল্যাগ
        }))
