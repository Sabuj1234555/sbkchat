from django.contrib.auth.models import User

if not User.objects.filter(username="_sobuj").exists():
    User.objects.create_superuser(
        username="_sobuj",
        email="sbk@gmail.com",
        password="programar369"
    )
