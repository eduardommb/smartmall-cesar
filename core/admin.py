from django.contrib import admin
from .models import Categoria, ItemPedido, Loja, Pedido, Produto

@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "responsavel", "categoria", "criado_em", "usuario")
    search_fields = ("nome", "cnpj", "responsavel", "usuario__username")
    list_filter = ("categoria", "criado_em")
    ordering = ("nome",)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "estoque")
    search_fields = ("nome",)
    list_filter = ()
    ordering = ("nome",)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "tipo_entrega", "criado_em")
    search_fields = ("id", "usuario__username")
    list_filter = ("tipo_entrega", "criado_em")
    ordering = ("-criado_em",)


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "produto", "quantidade", "preco_unitario")
    search_fields = ("pedido__id", "produto__nome")
    ordering = ("id",)
