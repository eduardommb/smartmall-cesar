from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Autenticação
    path('login/', views.CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro-lojista/', views.registrar_lojista, name='registrar_lojista'),
    path('registro-cliente/', views.registrar_cliente, name='registrar_cliente'),
    
    # Vitrine pública
    path('vitrine/', views.vitrine, name='vitrine'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:produto_id>/',views.adicionar_carrinho,name='adicionar_carrinho'),
    path('carrinho/remover/<int:produto_id>/',views.remover_carrinho,name='remover_carrinho'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/finalizar/', views.finalizar_pedido, name='finalizar_pedido'),
    path('pedido/confirmacao/<int:pedido_id>/', views.pedido_confirmacao, name='pedido_confirmacao'),
    
    # Dashboard do Lojista
    path('lojista/', views.lojista_dashboard, name='lojista_dashboard'),
    path('lojista/editar/', views.lojista_editar_perfil, name='lojista_editar_perfil'),
    path('lojista/produtos/adicionar/', views.lojista_adicionar_produto, name='lojista_adicionar_produto'),
    path('lojista/produtos/editar/<int:id>/', views.lojista_editar_produto, name='lojista_editar_produto'),
    path('lojista/produtos/remover/<int:id>/', views.lojista_remover_produto, name='lojista_remover_produto'),
    
    # Dashboard do Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/lojas/', views.gerenciar_lojas, name='admin_gerenciar_lojas'),
    
    path('catalogo/', views.painel_catalogo, name='painel_catalogo'),
    path('catalogo/adicionar/', views.adicionar_produto, name='adicionar_produto'),
    path('catalogo/editar/<int:id>/', views.editar_produto, name='editar_produto'),
    path('catalogo/remover/<int:id>/', views.remover_produto, name='remover_produto'),
    
    # Loja (Admin)
    path('lojas/', views.painel_lojas, name='painel_lojas'),
    path('lojas/adicionar/', views.cadastrar_loja, name='cadastrar_loja'),
    path('lojas/editar/<int:id>/', views.editar_loja, name='editar_loja'),
    path('lojas/remover/<int:id>/', views.remover_loja, name='remover_loja'),

    #ver loja
    path('loja/<int:loja_id>/', views.detalhe_loja, name='detalhe_loja'),
    
    # Busca autocomplete
    path('busca/autocomplete/', views.busca_autocomplete, name='busca_autocomplete'),
   
]
