import json
from urllib.parse import parse_qs
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async # sync_to_async যোগ করা হয়েছে
from rest_framework.authtoken.models import Token
from .models import ChatRoom, MessageDelivery, Messages

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        print("CONNECT START")
        self.room_group_name = None 

        query = parse_qs(self.scope["query_string"].decode())
        token_key = query.get("token", [None])[0]
        room_id = query.get("room_id", [None])[0]

        print("TOKEN:", token_key)
        print("ROOM ID:", room_id)

        try:
            # ডাটাবেজ কুয়েরিগুলোকে নিরাপদভাবে রান করানোর জন্য অ্যাসিঙ্ক-টু-সিঙ্ক করা হলো
            # কারণ সাধারণ ডিরেক্ট কুয়েরি অনেক সময় ASGI থ্রেড লক করে রিসেট এরর দেয়
            @async_to_sync
            async def get_records():
                # টোকেন ও ইউজার বের করা
                token = await sync_to_async(Token.objects.select_related('user').get)(key=token_key)
                user = token.user
                # রুম বের করা
                room = await sync_to_async(ChatRoom.objects.get)(id=room_id)
                return user, room

            # রেকর্ডগুলো নিয়ে আসা
            self.user, room = get_records()

            self.room_group_name = f"chat_{room_id}"

            # গ্রুপে যুক্ত করা
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            self.accept()
            print(f"Connected successfully: {self.user.username}")
            
            if not room.members.filter(id=self.user.id).exists():
                room.members.add(self.user)
                room.save()
                print(room.members.count())
                
            print(room.members.count())
            
                
            
            
            # পেন্ডিং বা অফলাইন মেসেজ পাঠানো (নিরাপদ উপায়ে)
            @async_to_sync
            async def get_pending_messages():
                pending_list = await sync_to_async(list)(
                    MessageDelivery.objects.filter(
                        user=self.user,
                        delivered=False,
                        message__room=room
                    ).select_related('message__user')
                )
                return pending_list

            pending = get_pending_messages()

            for item in pending:
                self.send(text_data=json.dumps({
                    "user_id": item.message.user.id,
                    "username": item.message.user.username,
                    "message": item.message.content,
                }))
                
                # ডেলিভারি স্ট্যাটাস আপডেট
                @async_to_sync
                async def save_item(delivery_item):
                    delivery_item.delivered = True
                    await sync_to_async(delivery_item.save)()
                
                save_item(item)

        except Exception as e:
            # এররটি যেন জ্যাঙ্গো টার্মিনালে পুঙ্খানুপুঙ্খ দেখা যায়
            import traceback
            print("CONNECT ERROR:")
            traceback.print_exc()
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
            print(msg)
            
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
