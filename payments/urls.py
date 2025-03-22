from django.urls import path
from . import views

urlpatterns = [
    path('cadastrar_aluno/',views.cadastrar_aluno, name='cadastrar_aluno'),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="sair")
]
