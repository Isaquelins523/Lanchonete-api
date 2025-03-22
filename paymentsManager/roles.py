from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        'subtrair_creditos': True,
        'cadastrar_aluno': True,
    }

class Aluno(AbstractUserRole):
    available_permissions = {
        'cadastrar_aluno': True,
        'add_creditos': True,
    }
