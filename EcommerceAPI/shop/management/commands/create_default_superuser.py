import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create default superuser if it does not exist"


    def handle(self, *args, **options):
        User = get_user_model()
        
        email=os.getenv("DJANGO_SUPERUSER_EMAIL")
        first_name=os.getenv("DJANGO_SUPERUSER_FIRST_NAME")
        last_name=os.getenv("DJANGO_SUPERUSER_LAST_NAME")
        password=os.getenv("DJANGO_SUPERUSER_PASSWORD")
        
        if not email or not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD manquants, skip."
            ))
            return
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f"Superuser {email} existe déjà, skip."))
            return

        User.objects.create_superuser(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser {email} créé."))