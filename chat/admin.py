from django.contrib import admin
from .models import ChatRoom,Messages,MessageDelivery



admin.site.register(ChatRoom)
admin.site.register(Messages)
admin.site.register(MessageDelivery)
