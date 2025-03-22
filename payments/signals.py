from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Users
from rolepermissions.roles import assign_role
from paymentsManager.roles import Admin, Aluno


@receiver(post_save, sender=Users)
def define_permissoes(sender, instance, created, **kwargs):
    if created:
        if instance.role == "ALN":
            assign_role(instance, Aluno)
        elif instance.role == "ADM":
            assign_role(instance, Admin)

