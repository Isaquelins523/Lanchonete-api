from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Users, Deposito
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
from django.contrib import messages


def cadastrar_aluno(request):
    if request.method == "GET":
        return render(request, 'cadastrar_aluno.html')

    if request.method == "POST":
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')


        if not nome or not email or not senha:
            messages.error(request, "Nome, email e senha são obrigatórios!")
            return redirect('cadastrar_aluno')

        if Users.objects.filter(email=email).exists():
            messages.error(request, "Esse email já está cadastrado!")
            return redirect('cadastrar_aluno')

        try:
            password_validation.validate_password(senha)
        except ValidationError as e:
            messages.error(request, f"Senha inválida: {', '.join(e.messages)}")
            return redirect('cadastrar_aluno')

        try:
            user = Users.objects.create_user(
                username=email,
                first_name=nome,
                email=email,
                password=senha,
                role='ALN'
            )
            print("Aluno cadastrado:", user)
            assign_role(user, Aluno)

            messages.success(request, "Cadastro realizado com sucesso! Faça login.")
            return redirect(reverse('login'))

        except Exception as e:
            print("Erro inesperado:", e)
            messages.error(request, f"Erro inesperado: {e}")
            return redirect('cadastrar_aluno')
    
    
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

        
        if user.role == 'ALN' and not user.id_aluno:
            user.save() 
        return redirect('deposito')  

    

def logout(request):
    request.session.flush()
    return redirect(reverse('login'))


sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)


@login_required
def deposito(request):
    if request.method == "GET":
        nome = request.user.first_name
        id_aluno = request.user.id_aluno
        return render(request, 'deposito.html', {'nome': nome, 'id_aluno': id_aluno})

    if request.method == "POST":
        valor = request.POST.get('valor')

        if not valor or float(valor) <= 0:
            messages.error(request, "Valor inválido. O valor deve ser maior que zero.")
            return redirect('deposito')

        try:
            valor = float(valor)
        except ValueError:
            messages.error(request, "Valor inválido.")
            return redirect('deposito')

        # Criar a preferência de pagamento
        payment_data = {
            "items": [{"title": "Depósito via Pix", "quantity": 1, "unit_price": valor}],
            "back_urls": {
                "success": request.build_absolute_uri(reverse('deposito_sucesso')) + f"?valor={valor}",
                "failure": request.build_absolute_uri(reverse('deposito_falha')),
            },
            "auto_return": "approved",
        }

        # Criando a preferência de pagamento
        result = sdk.preference().create(payment_data)
        payment = result["response"]

        # Pegando o link de pagamento gerado
        init_point = payment.get("init_point", "")

        # Redirecionando para a página de pagamento
        return redirect(init_point)


@login_required
def deposito_sucesso(request):
    # Pegando o valor do depósito via query param
    valor = request.GET.get('valor')
    
    if not valor:
        messages.error(request, "Erro ao processar o valor do depósito.")
        return redirect('deposito')

    try:
        # Verifica o status do pagamento com a API do Mercado Pago
        payment_id = request.GET.get('payment_id')
        payment_info = sdk.payment().get(payment_id)
        status = payment_info["response"].get("status")

        
        if status == "approved":
            user = request.user
            user.saldo += float(valor)
            user.save()

            
            Deposito.objects.create(usuario=user, valor=valor)

            messages.success(request, f"Depósito de R$ {valor} realizado com sucesso!")
            return redirect('saldo')

        else:
            messages.error(request, "Pagamento não aprovado. Tente novamente.")
            return redirect('deposito')

    except Exception as e:
        messages.error(request, f"Erro ao validar o pagamento: {e}")
        return redirect('deposito')


@login_required
def deposito_falha(request):
    messages.error(request, "O pagamento falhou. Tente novamente.")
    return redirect('deposito')


@login_required
def saldo(request):
    user = request.user
   
    depositos = Deposito.objects.filter(usuario=user).order_by('-data')

    return render(request, 'saldo.html', {
        "saldo": user.saldo,
        "depositos": depositos,
        "id_aluno": user.id_aluno
    })


@login_required
def admin_dashboard(request):
    if not request.user.role == 'ADM':
        return redirect('home')  
    
    aluno = None  

    if request.method == "POST":
        id_aluno = request.POST.get('id_aluno')
        valor_subtracao = request.POST.get('valor_subtracao')

        try:
            
            aluno = get_object_or_404(Users, id_aluno=id_aluno)

            if valor_subtracao:
                valor_subtracao = float(valor_subtracao)
                if valor_subtracao <= 0 or aluno.saldo < valor_subtracao:
                    messages.error(request, "Valor inválido ou saldo insuficiente.")
                    return render(request, 'admin_dashboard.html', {'aluno': aluno})

                # Subtrai o valor do saldo do aluno
                aluno.saldo -= valor_subtracao
                aluno.save()

                messages.success(request, f"R$ {valor_subtracao} subtraído do saldo do aluno com ID {id_aluno}.")
                return redirect('admin_dashboard')  

        except ValueError:
            return messages.error(request, "Valor de subtração inválido.")
            

    return render(request, 'admin_dashboard.html', {'aluno': aluno})



