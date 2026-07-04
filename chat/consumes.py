import json
from urllib.parse import parse_qs

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from rest_framework.authtoken.models import Token
from .models import ChatRoom, MessageDelivery, Messages


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        print("CONNECT START")
        
        # ডিফল্টভাবে room_group_name খালি রাখা হলো যেন ডিসকানেক্টে ক্র্যাশ না করে
        self.room_group_name = None 

        query = parse_qs(self.scope["query_string"].decode())
        token_key = query.get("token", [None])[0]
        room_id = query.get("room_id", [None])[0]

        print("TOKEN:", token_key)
        print("ROOM ID:", room_id)

        try:
            # ১. টোকেন দিয়ে ইউজার বের করা
            token = Token.objects.get(key=token_key)
            self.user = token.user

            # ২. রুমটি ডাটাবেজে আছে কিনা নিশ্চিত করা
            room = ChatRoom.objects.get(id=room_id)

            # ৩. নিরাপদ গ্রুপের নাম তৈরি (রুমের নামের বদলে আইডি ব্যবহার করা হলো)
            # এটি 'chat_1' এর মতো নিরাপদ নাম তৈরি করবে, যেখানে কোনো স্পেস বা নিষিদ্ধ অক্ষর থাকবে না
            self.room_group_name = f"chat_{room_id}"

            # ৪. গ্রুপে যুক্ত করা
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()
            print(f"Connected successfully: {self.user.username}")
            
            # ৫. পেন্ডিং বা অফলাইন মেসেজ পাঠানো
            pending = MessageDelivery.objects.filter(
                user=self.user,
                delivered=False,
                message__room=room
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
            # কোনো সমস্যা হলে কানেকশন রিজেক্ট করা
            self.close()

    def disconnect(self, close_code):
        print(f"Disconnected with code: {close_code}")

        # শুধুমাত্র গ্রুপের নাম সঠিকভাবে তৈরি হলেই গ্রুপ থেকে বাদ দেওয়া হবে
        if hasattr(self, "room_group_name") and self.room_group_name:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            room_id = data.get("room_id")
            
            if not message or not room_id:
                return

            room = ChatRoom.objects.get(id=room_id)

            # নতুন মেসেজ তৈরি
            msg = Messages.objects.create(
                user=self.user,
                room=room,
                content=message
            )
            
            # অন্য মেম্বারদের জন্য ডেলিভারি রেকর্ড তৈরি
            members = room.members.exclude(id=self.user.id)
            for member in members:
                MessageDelivery.objects.create(
                    message=msg,
                    user=member,
                    # আপনার মডেল অনুযায়ী ফিল্ডটি যুক্ত করা হলো
                )

            # গ্রুপে মেসেজ পাঠানো
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "message": msg.content,
                    "room_id": room.id,
                    "message_id": msg.id
                }
            )

        except Exception as e:
            print("RECEIVE ERROR:", e)

    def chat_message(self, event):
        try:
            # মেসেজ ডেলিভারি স্ট্যাটাস আপডেট
            MessageDelivery.objects.filter(
                message_id=event["message_id"],
                user=self.user
            ).update(delivered=True)
            
            # ক্লায়েন্টে মেসেজ পাঠানো
            self.send(text_data=json.dumps({
                "user_id": event["user_id"],
                "username": event["username"],
                "message": event["message"],
                "is_sender": self.user.id == event["user_id"],
                "room_id": event["room_id"],
                "message_id": event["message_id"]
            }))

        except Exception as e:
            print("SEND ERROR:", e)
