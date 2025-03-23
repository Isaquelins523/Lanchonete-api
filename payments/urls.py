from django.urls import path
from . import views

urlpatterns = [
    path('cadastrar_aluno/',views.cadastrar_aluno, name='cadastrar_aluno'),
    path('', views.login, name="login"),
    path('deposito/', views.deposito, name='deposito'),
    path('saldo/', views.saldo , name="saldo"),
    path('deposito_sucesso/', views.deposito_sucesso, name='deposito_sucesso'),
    path('deposito_falha/', views.deposito_falha, name='deposito_falha'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.logout, name="sair"),
]
