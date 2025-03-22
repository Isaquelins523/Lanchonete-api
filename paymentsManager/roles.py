from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        'cadastrar_usuario': True,
        'subtrair_creditos': True,
        'cadastrar_aluno': True,
    }

class Aluno(AbstractUserRole):
    available_permissions = {
        'cadastrar_usuario': True,
        'add_creditos': True,
    }
