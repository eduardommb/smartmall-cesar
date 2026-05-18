from collections import Counter
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from .forms import LojaForm, LojistaRegistrationForm, ProdutoForm
from .models import Categoria, ItemPedido, Loja, Pedido, Produto


class CustomLoginView(LoginView):
    def get_success_url(self):
        if self.request.user.is_staff:
            return "/admin-dashboard/"
        elif hasattr(self.request.user, "loja"):
            return "/lojista/"
        return "/vitrine/"


def logout_view(request):
    from django.contrib.auth import logout as auth_logout

    auth_logout(request)
    return render(request, "registration/logout.html")


def painel_catalogo(request):
    produtos = Produto.objects.all()
    return render(request, "core/admin/catalogo.html", {"produtos": produtos})


def home(request):
    return render(request, "core/public/home.html")


def vitrine(request):
    """
    Vitrine pública de lojas, com filtro por categoria (?categoria=<id>)
    e busca por nome de loja ou produto (?q=...).
    """
    categorias = Categoria.objects.all()
    categoria_id = request.GET.get("categoria")
    query = request.GET.get("q", "").strip()

    lojas = Loja.objects.select_related("categoria").all()

    # Filtro por categoria
    if categoria_id:
        lojas = lojas.filter(categoria_id=categoria_id)

    # Filtro por busca de lojas (nome)
    if query:
        lojas = lojas.filter(Q(nome__icontains=query))

    # Buscar produtos se houver query
    produtos_encontrados = []
    if query:
        produtos_encontrados = Produto.objects.select_related(
            "loja", "loja__categoria"
        ).filter(
            Q(nome__icontains=query)
            | Q(descricao__icontains=query)
            | Q(loja__categoria__nome__icontains=query)
        )[:20]  # Limitar a 20 resultados

    return render(
        request,
        "core/public/vitrine.html",
        {
            "categorias": categorias,
            "lojas": lojas,
            "query": query,
            "produtos_encontrados": produtos_encontrados,
        },
    )


def busca_autocomplete(request):
    """
    View para autocomplete da busca em tempo real.
    Retorna uma lista de lojas e produtos que correspondem à query.
    """
    query = request.GET.get("q", "").strip()

    if not query or len(query) < 2:
        return JsonResponse({"results": []})

    # Buscar lojas
    lojas = Loja.objects.filter(Q(nome__icontains=query))[:5]

    # Buscar produtos
    produtos = Produto.objects.select_related("loja").filter(Q(nome__icontains=query))[
        :5
    ]

    results = []

    # Adicionar lojas aos resultados
    for loja in lojas:
        results.append(
            {
                "type": "loja",
                "id": loja.id,
                "name": loja.nome,
                "category": loja.categoria.nome if loja.categoria else "",
                "url": f"/loja/{loja.id}/",
            }
        )

    # Adicionar produtos aos resultados
    for produto in produtos:
        results.append(
            {
                "type": "produto",
                "id": produto.id,
                "name": produto.nome,
                "loja": produto.loja.nome if produto.loja else "",
                "preco": str(produto.preco) if produto.preco else "",
                "url": f"/loja/{produto.loja.id}/" if produto.loja else "",
            }
        )

    return JsonResponse({"results": results})


@login_required
@user_passes_test(lambda u: u.is_staff)
def painel_lojas(request):
    lojas = Loja.objects.select_related("usuario", "categoria").all()
    return render(request, "core/admin/lojas.html", {"lojas": lojas})


@login_required
@user_passes_test(lambda u: u.is_staff)
def cadastrar_loja(request):
    if request.method == "POST":
        form = LojaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Loja cadastrada com sucesso")
            return redirect("painel_lojas")
    else:
        form = LojaForm()

    return render(request, "core/admin/loja_form.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_loja(request, id):
    loja = get_object_or_404(Loja, id=id)
    if request.method == "POST":
        form = LojaForm(request.POST, request.FILES, instance=loja)
        if form.is_valid():
            form.save()
            messages.success(request, "Loja atualizada com sucesso")
            return redirect("painel_lojas")
    else:
        form = LojaForm(instance=loja)
    return render(
        request, "core/admin/loja_form.html", {"form": form, "acao": "Editar"}
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def remover_loja(request, id):
    loja = get_object_or_404(Loja, id=id)
    if request.method == "POST":
        loja.delete()
        messages.success(request, "Loja removida com sucesso")
        return redirect("painel_lojas")
    return render(request, "core/admin/loja_confirm_delete.html", {"loja": loja})


@login_required
@user_passes_test(lambda u: u.is_staff)
def adicionar_produto(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso!")
            return redirect("painel_catalogo")
    else:
        form = ProdutoForm()
    contexto = {"form": form, "acao": "Adicionar"}
    return render(request, "core/admin/produto_form.html", contexto)


@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_produto(request, id):
    if not request.user.is_staff:
        messages.error(request, "Acesso restrito a administradores.")
        return redirect("vitrine")

    produto = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado com sucesso!")
            return redirect("painel_catalogo")
    else:
        form = ProdutoForm(instance=produto)

    contexto = {"form": form, "acao": "Editar"}
    return render(request, "core/admin/produto_form.html", contexto)


def remover_produto(request, id):
    if not request.user.is_staff:
        messages.error(request, "Acesso restrito a administradores.")
        return redirect("vitrine")

    produto = get_object_or_404(Produto, id=id)
    if request.method == "POST":
        produto.delete()
        return redirect("painel_catalogo")

    return render(
        request, "core/admin/produto_confirm_delete.html", {"produto": produto}
    )


def registrar_lojista(request):
    if request.method == "POST":
        form = LojistaRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(
                request, f"Loja cadastrada com sucesso! Bem-vindo, {username}."
            )
            # Faz login automaticamente após o registro
            auth_login(request, form.instance)
            return redirect("lojista_dashboard")
    else:
        form = LojistaRegistrationForm()

    return render(request, "registration/registro_lojista.html", {"form": form})


@login_required
def lojista_dashboard(request):
    # Verifica se o usuário tem uma loja associada
    if not hasattr(request.user, "loja"):
        messages.error(
            request, "Você não tem uma loja associada. Contate o administrador."
        )
        return redirect("vitrine")

    loja = request.user.loja
    produtos = loja.produtos.all()

    context = {
        "loja": loja,
        "produtos": produtos,
        "total_produtos": produtos.count(),
        "estoque_baixo": produtos.filter(estoque__lt=5).count(),
    }

    return render(request, "core/lojista/dashboard.html", context)


@login_required
def lojista_editar_perfil(request):
    if not hasattr(request.user, "loja"):
        messages.error(
            request, "Você não tem uma loja associada. Contate o administrador."
        )
        return redirect("vitrine")

    loja = request.user.loja

    if request.method == "POST":
        form = LojaForm(request.POST, request.FILES, instance=loja)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil da loja atualizado com sucesso!")
            return redirect("lojista_dashboard")
    else:
        form = LojaForm(instance=loja)

    return render(
        request, "core/lojista/editar_perfil.html", {"form": form, "loja": loja}
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    total_lojas = Loja.objects.count()
    total_produtos = Produto.objects.count()
    total_categorias = Categoria.objects.count()

    # Lojistas recentes (últimos 5)
    lojas_recentes = Loja.objects.select_related("usuario", "categoria").order_by(
        "-criado_em"
    )[:5]

    context = {
        "total_lojas": total_lojas,
        "total_produtos": total_produtos,
        "total_categorias": total_categorias,
        "lojas_recentes": lojas_recentes,
    }

    return render(request, "core/admin/dashboard.html", context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def gerenciar_lojas(request):
    lojas = Loja.objects.select_related("usuario", "categoria").all()
    return render(request, "core/admin/gerenciar_lojas.html", {"lojas": lojas})


@login_required
def lojista_adicionar_produto(request):
    if not hasattr(request.user, "loja"):
        messages.error(request, "Você não tem uma loja associada.")
        return redirect("vitrine")

    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.loja = request.user.loja
            produto.save()
            messages.success(request, "Produto cadastrado com sucesso!")
            return redirect("lojista_dashboard")
    else:
        form = ProdutoForm()

    return render(
        request, "core/lojista/produto_form.html", {"form": form, "acao": "Adicionar"}
    )


@login_required
def lojista_editar_produto(request, id):
    if not hasattr(request.user, "loja"):
        messages.error(request, "Você não tem uma loja associada.")
        return redirect("vitrine")

    produto = get_object_or_404(Produto, id=id, loja=request.user.loja)

    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado com sucesso!")
            return redirect("lojista_dashboard")
    else:
        form = ProdutoForm(instance=produto)

    return render(
        request, "core/lojista/produto_form.html", {"form": form, "acao": "Editar"}
    )


@login_required
def lojista_remover_produto(request, id):
    if not hasattr(request.user, "loja"):
        messages.error(request, "Você não tem uma loja associada.")
        return redirect("vitrine")

    produto = get_object_or_404(Produto, id=id, loja=request.user.loja)

    if request.method == "POST":
        produto.delete()
        messages.success(request, "Produto removido com sucesso!")
        return redirect("lojista_dashboard")

    return render(
        request, "core/lojista/produto_confirm_delete.html", {"produto": produto}
    )


def detalhe_loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    produtos = Produto.objects.filter(loja=loja)

    return render(
        request, "core/public/detalhe_loja.html", {"loja": loja, "produtos": produtos}
    )



def carrinho(request):
    carrinho_ids = request.session.get("carrinho", [])
    itens, total = _resumo_carrinho(carrinho_ids)
    quantidade_total = sum(item["quantidade"] for item in itens)

    return render(
        request,
        "core/public/carrinho.html",
        {
            "itens": itens,
            "total": total,
            "quantidade_total": quantidade_total,
        },
    )


def adicionar_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    carrinho = request.session.get("carrinho", [])

    carrinho.append(produto.id)

    request.session["carrinho"] = carrinho

    return redirect("carrinho")


@require_POST
def remover_carrinho(request, produto_id):
    carrinho = request.session.get("carrinho", [])

    if produto_id in carrinho:
        carrinho.remove(produto_id)

    request.session["carrinho"] = carrinho

    return redirect("carrinho")


def _resumo_carrinho(carrinho_ids):
    contagem = Counter(carrinho_ids)
    produtos_por_id = Produto.objects.in_bulk(contagem.keys())
    itens = []
    total = Decimal("0.00")

    for produto_id, quantidade in contagem.items():
        produto = produtos_por_id.get(produto_id)
        if not produto:
            continue
        subtotal = produto.preco * quantidade
        total += subtotal
        itens.append(
            {
                "produto": produto,
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

    itens.sort(key=lambda item: item["produto"].nome.lower())
    return itens, total


@login_required
def checkout(request):
    carrinho_ids = request.session.get("carrinho", [])
    itens, total = _resumo_carrinho(carrinho_ids)

    if not itens:
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("carrinho")

    return render(
        request,
        "core/public/checkout.html",
        {
            "itens": itens,
            "total": total,
            "tipo_entrega_padrao": Pedido.TipoEntrega.RETIRADA,
        },
    )


@login_required
@require_POST
def finalizar_pedido(request):
    carrinho_ids = request.session.get("carrinho", [])
    if not carrinho_ids:
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("carrinho")

    tipo_entrega = request.POST.get("tipo_entrega", Pedido.TipoEntrega.RETIRADA)
    if tipo_entrega != Pedido.TipoEntrega.RETIRADA:
        messages.error(request, "Tipo de entrega inválido.")
        return redirect("checkout")

    with transaction.atomic():
        contagem = Counter(carrinho_ids)
        produtos = Produto.objects.select_for_update().in_bulk(contagem.keys())

        if len(produtos) != len(contagem):
            messages.error(request, "Há produtos indisponíveis no carrinho.")
            return redirect("carrinho")

        for produto_id, quantidade in contagem.items():
            produto = produtos[produto_id]
            if produto.estoque < quantidade:
                messages.error(
                    request,
                    f"Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque}.",
                )
                return redirect("checkout")

        pedido = Pedido.objects.create(usuario=request.user, tipo_entrega=tipo_entrega)
        itens_pedido = []

        for produto_id, quantidade in contagem.items():
            produto = produtos[produto_id]
            itens_pedido.append(
                ItemPedido(
                    pedido=pedido,
                    produto=produto,
                    quantidade=quantidade,
                    preco_unitario=produto.preco,
                )
            )
            produto.estoque -= quantidade
            produto.save(update_fields=["estoque"])

        ItemPedido.objects.bulk_create(itens_pedido)

    request.session["carrinho"] = []
    messages.success(request, f"Pedido #{pedido.id} finalizado com sucesso!")
    return redirect("pedido_confirmacao", pedido_id=pedido.id)


@login_required
def pedido_confirmacao(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.select_related("usuario").prefetch_related("itens__produto"),
        id=pedido_id,
        usuario=request.user,
    )
    total = sum((item.preco_unitario * item.quantidade for item in pedido.itens.all()), Decimal("0.00"))
    return render(
        request,
        "core/public/pedido_confirmacao.html",
        {"pedido": pedido, "total": total},
    )
