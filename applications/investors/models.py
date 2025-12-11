from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Investor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="investor_profile")
    document_id = models.CharField(max_length=20, unique=True, help_text="DNI/Pasaporte")
    phone = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ("LOW", "Bajo"),
            ("MEDIUM", "Medio"),
            ("HIGH", "Alto"),
        ],
        default="MEDIUM",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inversor: {self.user.username}"
