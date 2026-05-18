from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from core.models import Categoria, ItemPedido, Loja, Pedido, Produto


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cliente", email="cliente@example.com", password="senha12345"
        )
        self.categoria = Categoria.objects.create(nome="Tecnologia")
        self.loja = Loja.objects.create(
            nome="Loja Checkout",
            cnpj="98.765.432/0001-11",
            responsavel="Responsável Checkout",
            categoria=self.categoria,
        )
        self.produto = Produto.objects.create(
            nome="Notebook", preco="1200.00", estoque=5, loja=self.loja
        )

    def _set_carrinho(self, ids):
        session = self.client.session
        session["carrinho"] = ids
        session.save()

    def test_checkout_exige_autenticacao(self):
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_checkout_com_carrinho_vazio_redireciona(self):
        self.client.login(username="cliente", password="senha12345")
        response = self.client.get(reverse("checkout"), follow=True)

        self.assertRedirects(response, reverse("carrinho"))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Seu carrinho está vazio.", messages)

    def test_finalizar_pedido_cria_pedido_baixa_estoque_e_limpa_carrinho(self):
        self.client.login(username="cliente", password="senha12345")
        self._set_carrinho([self.produto.id, self.produto.id])

        response = self.client.post(
            reverse("finalizar_pedido"),
            {"tipo_entrega": Pedido.TipoEntrega.RETIRADA},
            follow=False,
        )

        self.assertEqual(Pedido.objects.count(), 1)
        pedido = Pedido.objects.get()
        self.assertEqual(pedido.usuario, self.user)
        self.assertEqual(pedido.tipo_entrega, Pedido.TipoEntrega.RETIRADA)
        self.assertEqual(ItemPedido.objects.filter(pedido=pedido).count(), 1)
        item = ItemPedido.objects.get(pedido=pedido)
        self.assertEqual(item.quantidade, 2)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 3)
        self.assertEqual(self.client.session.get("carrinho"), [])
        self.assertRedirects(
            response,
            reverse("pedido_confirmacao", args=[pedido.id]),
            fetch_redirect_response=False,
        )

    def test_finalizar_pedido_com_estoque_insuficiente_nao_cria_pedido(self):
        self.client.login(username="cliente", password="senha12345")
        self._set_carrinho([self.produto.id] * 6)

        response = self.client.post(
            reverse("finalizar_pedido"),
            {"tipo_entrega": Pedido.TipoEntrega.RETIRADA},
            follow=True,
        )

        self.assertRedirects(response, reverse("checkout"))
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(ItemPedido.objects.count(), 0)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 5)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Estoque insuficiente" in mensagem for mensagem in messages))
