from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_super_admin = models.BooleanField(default=False)

    ecoles = models.ManyToManyField("ECOLE.Ecole", blank=True)
# Create your models here.
