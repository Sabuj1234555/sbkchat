from rest_framework import serializers
from .models import ChatRoom

class RoomSerializers(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = "__all__"