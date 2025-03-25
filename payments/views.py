from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Users, Deposito
import mercadopago
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rolepermissions.roles import assign_role
from paymentsManager.roles import Aluno
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST

sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

# Função de cadastro de aluno
def cadastrar_aluno(request):
    if request.method == "GET":
        return render(request, 'cadastrar_aluno.html')

    if request.method == "POST":
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        foto = request.FILES.get('foto')

        if not nome or not email or not senha or not foto:
            messages.error(request, "Nome, email, senha e foto são obrigatórios!")
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
            assign_role(user, Aluno)

            if foto:
                ext = foto.name.split('.')[-1]
                new_filename = f'foto_{user.id_aluno}.{ext}'

                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'alunos_fotos'))

                filename = fs.save(new_filename, foto)
                user.foto = f'alunos_fotos/{filename}'
                user.save()

            messages.success(request, "Cadastro realizado com sucesso! Faça login.")
            return redirect(reverse('login'))

        except Exception as e:
            print("Erro inesperado:", e)
            messages.error(request, f"Erro inesperado: {e}")
            return redirect('cadastrar_aluno')

# Função de login
def login(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect(reverse('deposito') if request.user.role == 'ALN' else reverse('admin_dashboard'))
        return render(request, 'login.html')

    elif request.method == "POST":
        login = request.POST.get('email')
        senha = request.POST.get('senha')

        user = auth.authenticate(username=login, password=senha)

        if not user:
            messages.error(request, 'Usuário ou senha inválidos')
            return redirect('login')

        auth.login(request, user)

        if user.role == 'ALN':
            return redirect('deposito')
        elif user.role == 'ADM':
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Usuário sem permissão.')
            return redirect('login')

# Função de logout
def logout(request):
    request.session.flush()
    return redirect(reverse('login'))

# Função de depósito
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
            "success": request.build_absolute_uri(reverse('saldo')),
            "failure": request.build_absolute_uri(reverse('deposito_falha')),
        },
        "auto_return": "approved",
        "notification_url": request.build_absolute_uri(reverse('mercado_pago_webhook')),
        "external_reference": str(request.user.id_aluno),
        "payment_methods": {
            "excluded_payment_types": [{"id": "ticket"}, {"id": "credit_card"}, {"id": "debit_card"}]  
    }
}


        # Criando a preferência de pagamento
        result = sdk.preference().create(payment_data)
        payment = result["response"]

        # Pegando o link de pagamento gerado
        init_point = payment.get("init_point", "")

        # Redirecionando para a página de pagamento
        return redirect(init_point)

# Função de sucesso do depósito
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

            messages.success(request, f"Depósito confirmado! Saldo atualizado para R$ {request.user.saldo:.2f}")
            return redirect('saldo')

        else:
            messages.error(request, "Pagamento não aprovado. Tente novamente.")
            return redirect('deposito')

    except Exception as e:
        messages.error(request, f"Erro ao validar o pagamento: {e}")
        return redirect('deposito')

# Função de falha no depósito
@login_required
def deposito_falha(request):
    messages.error(request, "O pagamento falhou. Tente novamente.")
    return redirect('deposito')

# Função de saldo
@login_required
def saldo(request):
    user = request.user
    depositos = Deposito.objects.filter(usuario=user).order_by('-data')
    return render(request, 'saldo.html', {"saldo": user.saldo, "depositos": depositos, "id_aluno": user.id_aluno})

# Função de dashboard administrativo
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


def home(request):
    return render(request, 'home.html')



@csrf_exempt
def mercado_pago_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        # Verificação básica de origem (opcional mas recomendado)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for not in ['181.209.63.207', '181.209.63.208', '181.209.63.209']:
            return JsonResponse({'error': 'IP não autorizado'}, status=403)

        payload = json.loads(request.body)
        print("Payload recebido:", payload)  # Para debug

        # Processar apenas notificações do tipo payment
        if payload.get("type") == "payment":
            payment_id = payload.get("data", {}).get("id")
            if not payment_id:
                return JsonResponse({'error': 'ID de pagamento ausente'}, status=400)

            # Obter detalhes do pagamento
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info["response"]
            print("Dados do pagamento:", payment_data)  # Para debug

            # Verificar se o pagamento foi aprovado via PIX
            if payment_data.get("status") == "approved" and payment_data.get("payment_method_id") == "pix":
                user_id = payment_data.get("external_reference")
                if not user_id:
                    return JsonResponse({'error': 'external_reference ausente'}, status=400)

                try:
                    user = Users.objects.get(id_aluno=user_id)
                    amount = float(payment_data["transaction_amount"])
                    
                    # Atualizar saldo
                    user.saldo += amount
                    user.save()
                    
                    # Registrar o depósito
                    Deposito.objects.create(
                        usuario=user,
                        valor=amount,
                        comprovante=payment_id,
                        status="approved"
                    )
                    
                    print(f"Saldo atualizado para o usuário {user_id}. Novo saldo: {user.saldo}")
                    return JsonResponse({'status': 'success'})

                except Users.DoesNotExist:
                    return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
                except Exception as e:
                    print(f"Erro ao atualizar saldo: {str(e)}")
                    return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'status': 'ignored'}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        print(f"Erro geral no webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)