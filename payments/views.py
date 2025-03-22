from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Users
import mercadopago
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rolepermissions.roles import assign_role
from paymentsManager.roles import Aluno
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required


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

       
        return redirect('login')
    
    
def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect(reverse('deposito'))
        return render(request, 'login.html')
        
    elif request.method == "POST":
        login = request.POST.get('email')
        senha = request.POST.get('senha')

        user = auth.authenticate(username=login, password=senha)

        if not user:
            return HttpResponse('Usuário ou senha inválidos')
            
        auth.login(request, user)
        return redirect('deposito')  

    

def logout(request):
    request.session.flush()
    return redirect(reverse('login'))


sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

@login_required
def deposito(request):
    if request.method == "GET":
        return render(request, 'deposito.html')

    if request.method == "POST":
        valor = request.POST.get('valor')

        if not valor or float(valor) <= 0:
            return HttpResponse("Valor inválido. O valor deve ser maior que zero.")

        try:
            valor = float(valor)
        except ValueError:
            return HttpResponse("Valor inválido.")

        # Criar a preferência de pagamento
        payment_data = {
            "items": [
                {
                    "id": "1",
                    "title": "Depósito na carteira",
                    "description": f"Depositar R${valor:.2f} na carteira",
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": valor,
                },
            ],
            "back_urls": {
                "success": "http://localhost:8000/success/",
                "failure": "http://localhost:8000/failure/",
                "pending": "http://localhost:8000/pending/",
            },
            "auto_return": "all",
            "default_payment_method_id": "pix", 
            "excluded_payment_types": [
                {"id": "ticket"},
                {"id": "credit_card"},
                {"id": "debit_card"},
                {"id": "bank_transfer"},
                {"id": "atm"},
            ],
            "excluded_payment_methods": [
                {"id": "visa"},
                {"id": "master"},
            ],
        }

        # Criando a preferência de pagamento
        result = sdk.preference().create(payment_data)
        payment = result["response"]

        # Pegando o link de pagamento gerado
        init_point = payment["init_point"]

        # Redirecionando para a página de pagamento
        return redirect(init_point)