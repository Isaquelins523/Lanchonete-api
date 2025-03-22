from django.shortcuts import render, redirect
from django.http import HttpResponse
from rolepermissions.decorators import has_permission_decorator
from .models import Users
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rolepermissions.roles import assign_role
from paymentsManager.roles import Aluno
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import auth

@has_permission_decorator('cadastrar_aluno')
def cadastrar_aluno(request):
    if request.method == "GET":
        return render(request, 'cadastrar_aluno.html')

    if request.method == "POST":
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        
        if not email or not senha:
            return HttpResponse('Email ou senha não podem ser vazios')

        
        user = Users.objects.filter(email=email)
        if user.exists():
            return HttpResponse('Email já existe')

       
        try:
            password_validation.validate_password(senha)
        except ValidationError as e:
            return HttpResponse(f"Senha inválida: {', '.join(e.messages)}")

        
        user = Users.objects.create_user(username=email, email=email, password=senha, role='ALN')

        assign_role(user, Aluno)

       
        return HttpResponse('sucesso') 
    
    
def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect(reverse('login'))
        return render(request, 'login.html')
        
    elif request.method == "POST":
        login = request.POST.get('email')
        senha = request.POST.get('senha')

        user = auth.authenticate(username=login, password=senha)

        if not user:
            return HttpResponse('Usuário inválido')
            
        auth.login(request, user)
        return HttpResponse('Usuário logado com sucesso!')
    

def logout(request):
    request.session.flush()
    return redirect(reverse('login'))