from django.urls import path
from .views import AuthView,CheckUserView

urlpatterns = [
    path("auth/",AuthView.as_view()),
    path("check-auth/",CheckUserView.as_view())
]
