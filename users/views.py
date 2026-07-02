from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token


class AuthView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        email = request.data.get("email", "").strip()

        # Validation
        if not username or not password:
            return Response(
                {
                    "success": False,
                    "message": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # User exists -> Login
        if User.objects.filter(username=username).exists():

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is None:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid username or password."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "success": True,
                    "message": "Login successful.",
                    "token": token.key,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    }
                },
                status=status.HTTP_200_OK
            )

        # User doesn't exist -> Create account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "success": True,
                "message": "Account created successfully.",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            },
            status=status.HTTP_201_CREATED
        )


class CheckUserView(APIView):
    def get(self,request):
        if request.user.is_authenticated:
            return Response({"user_valid":True})
        return Response({"user_valid":False})