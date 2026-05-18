from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from .models import Categoria, Loja, Produto


class LojistaRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
    )
    nome_loja = forms.CharField(
        label="Nome da Loja",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Nome da sua loja"}),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        max_length=18,
        widget=forms.TextInput(attrs={"placeholder": "XX.XXX.XXX/XXXX-XX"}),
    )
    responsavel = forms.CharField(
        label="Nome do Responsável",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Nome completo"}),
    )
    categoria = forms.ModelChoiceField(
        label="Categoria",
        queryset=Categoria.objects.all(),
        required=True,
        empty_label="Selecione uma categoria",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Usuário para login"}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj")
        if Loja.objects.filter(cnpj=cnpj).exists():
            raise forms.ValidationError("Este CNPJ já está cadastrado.")
        return cnpj

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.email = self.cleaned_data["email"]
        user.is_active = True
        if commit:
            loja = Loja.objects.create(
                nome=self.cleaned_data["nome_loja"],
                cnpj=self.cleaned_data["cnpj"],
                responsavel=self.cleaned_data["responsavel"],
                categoria=self.cleaned_data["categoria"],
                usuario=user,
            )
        return user


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "preco", "estoque", "descricao", "imagem", "loja"]
        widgets = {
            "loja": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se é um lojista, a loja será definida na view
        # O campo loja pode ser ocultado via template se necessário


class LojaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].required = False

    class Meta:
        model = Loja
        fields = ["nome", "cnpj", "responsavel", "categoria", "imagem"]
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get("cnpj")
        # Só verifica duplicidade se for uma nova loja (não edição)
        if not self.instance.pk:
            if Loja.objects.filter(cnpj=cnpj).exists():
                raise forms.ValidationError("CNPJ já cadastrado")
        return cnpj

class ClienteRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
    )
    first_name = forms.CharField(
        label="Nome",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Seu primeiro nome"}),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Seu sobrenome"}),
    )

    class Meta:
        model = User
        # O Django já coloca as senhas automaticamente por causa do UserCreationForm
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Nome de usuário para login"}),
        }

    def clean_email(self):
        # Evita que dois clientes usem o mesmo e-mail
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def save(self, commit=True):
        # Salva as informações básicas de login
        user = super().save(commit=False)
        # Associa as informações extras que pedimos
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = True
        
        if commit:
            user.save()
            # Note que AQUI não criamos a Loja. Ele é apenas um User comum!
            
        return user