from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ChatRoom
from .serializers import RoomSerializers



class CreateRoomView(APIView):
    def post(self,request):
        
        room_name = request.data.get("room_name")
        
        room = ChatRoom.objects.create(
            user=request.user,
            name = room_name
        )
        return Response({"room_name":room.name,"room_id":room.id})
    
class GetHomeView(APIView):
    def get(self,request):
        
        room = ChatRoom.objects.all()
        serializer = RoomSerializers(room,many=True)
        return Response(serializer.data)
        
        
        



