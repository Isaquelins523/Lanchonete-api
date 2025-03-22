from django.urls import path
from . import views

urlpatterns = [
    path('cadastrar_aluno/',views.cadastrar_aluno, name='cadastrar_aluno'),
    path('', views.login, name="login"),
    path('deposito/', views.deposito, name='deposito'),
    path('logout/', views.logout, name="sair")
]
