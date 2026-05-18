from django.contrib.auth.models import User
from django.db import models


class Categoria(models.Model):
    nome = models.CharField("Nome", max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Loja(models.Model):
    nome = models.CharField("Nome da Loja", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    responsavel = models.CharField("Responsável", max_length=255)
    usuario = models.OneToOneField(
        User, on_delete=models.PROTECT, null=True, blank=True, related_name="loja"
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lojas",
        verbose_name="Categoria",
    )

    imagem = models.ImageField(
        "Imagem da loja", upload_to="lojas/", blank=True, null=True
    )

    class Meta:
        verbose_name = "Loja"
        verbose_name_plural = "Lojas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField("Nome", max_length=200)
    preco = models.DecimalField("Preco", max_digits=10, decimal_places=2)
    estoque = models.IntegerField("Estoque", default=0)
    descricao = models.TextField("Descrição", blank=True, null=True)
    imagem = models.ImageField("Imagem", upload_to="produtos/", blank=True, null=True)
    loja = models.ForeignKey(
        "Loja",
        on_delete=models.CASCADE,
        related_name="produtos",
        verbose_name="Loja",
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.loja:
            return f"{self.nome} ({self.loja.nome})"
        return self.nome


class Pedido(models.Model):
    class TipoEntrega(models.TextChoices):
        RETIRADA = "RETIRADA", "Retirada no Shopping"

    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="pedidos")
    tipo_entrega = models.CharField(
        "Tipo de entrega",
        max_length=20,
        choices=TipoEntrega.choices,
        default=TipoEntrega.RETIRADA,
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Pedido #{self.pk}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="+")
    quantidade = models.PositiveIntegerField("Quantidade")
    preco_unitario = models.DecimalField("Preço unitário", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome}"
