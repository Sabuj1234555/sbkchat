from django.urls import path
from rest_framework.authtoken import views
from .views import CreateRoomView,GetHomeView



urlpatterns = [
    path("api-auth-token/",views.obtain_auth_token),
    path('create-room',CreateRoomView.as_view()),
    path("get-home-room/",GetHomeView.as_view()),
]
