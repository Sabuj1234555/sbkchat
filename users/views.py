from django.contrib.auth.models import User
from django.contrib.auth import login,authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer


class AuthView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def post(self,request):
      
        username  = request.data.get("username")
        password = request.data.get("password")
        
    
        
        if not username and password:
            return Response(
                {
                    "message":"username and password are require",
                    
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.filter(username=username).first()
        
        if user:
            user = authenticate(request,username=username,password=password)
            
            if not user:
                return Response(
                   {
                        "message":"Wrong password"
                   },
                   status=status.HTTP_400_BAD_REQUEST
                )
            token ,created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "message":"login successful",
                    "token":token.key,
                    "user":{
                        "id":user.id,
                        "username":user.username,
                        "password":user.password,
                        "email":user.email,
                    }
                },
                status=status.HTTP_202_ACCEPTED
            )
        
        # user not found create user
        
        user = User.objects.create_user(
            username=username,
            password=password
        )
        token ,created = Token.objects.get_or_create(user=user)
        
        return Response(
            {
                "message":"account created successfully",
                "token":token.key
            },
            status=status.HTTP_201_CREATED
        )
                