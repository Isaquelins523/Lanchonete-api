from django.db import models
from django.contrib.auth.models import AbstractUser


class Users(AbstractUser):
    choices_role = (('ADM', 'Admin'),
                   ('ALN', 'Aluno'))
    role = models.CharField(max_length=3, choices=choices_role)
   