from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import os


class Users(AbstractUser):
    choices_role = (('ADM', 'Admin'),
                   ('ALN', 'Aluno'))
    role = models.CharField(max_length=3, choices=choices_role)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    id_aluno = models.CharField(max_length=4, unique=True, blank=True, null=True)
    foto = models.ImageField(upload_to='alunos_fotos/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id_aluno:  
            self.id_aluno = self.gerar_id_aluno()
        super().save(*args, **kwargs)


                
        if self.foto and not self.pk:  # not self.pk significa que é um novo usuário
            # Obtém a extensão do arquivo original
            ext = os.path.splitext(self.foto.name)[1]
            # Define o novo nome do arquivo
            self.foto.name = f'alunos_fotos/foto_{self.id_aluno}{ext}'
        
        super().save(*args, **kwargs)


    def gerar_id_aluno(self):
      
        while True:
            id_gerado = str(random.randint(1000, 9999))  # Gera um número entre 1000 e 9999
            if not Users.objects.filter(id_aluno=id_gerado).exists():  
                return id_gerado

   

class Deposito(models.Model):
    usuario = models.ForeignKey(Users, on_delete=models.CASCADE)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)
