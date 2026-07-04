from django.db import models
from django.contrib.auth.models import User

class ChatRoom(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="room_creator")
    name = models.CharField(max_length=100,unique=True)
    members = models.ManyToManyField(User,related_name="room_joiner",blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return self.name
    
class Messages(models.Model):
    room = models.ForeignKey(ChatRoom,on_delete=models.CASCADE,related_name="message")
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self) -> str:
        return self.room.name
    
class MessageDelivery(models.Model):
    message = models.ForeignKey(
        Messages,
        on_delete=models.CASCADE,
        related_name="deliveries"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

    class Meta:
        unique_together = ("message", "user")
