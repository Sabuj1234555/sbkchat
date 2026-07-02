from django.urls import path
from rest_framework.authtoken import views



urlpatterns = [
    path("api-auth-token/",views.obtain_auth_token)
]
