# noticias/views_auth.py
import random
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone

User = get_user_model()

# ===== Forms =====
class ResetEmailForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "seuemail@exemplo.com"})
    )

class CodeForm(forms.Form):
    code = forms.CharField(min_length=6, max_length=6)

# ===== Helpers =====
def _gen_code() -> str:
    return f"{random.randint(0, 999999):06d}"

def _cache_key(email: str) -> str:
    return f"pwdreset:{email.lower()}"

def _store_code(email: str, code: str, minutes: int = 10) -> None:
    expires_at = timezone.now() + timedelta(minutes=minutes)
    cache.set(_cache_key(email), {"code": code, "expires_at": expires_at}, timeout=minutes * 60)

def _get_code_bundle(email: str):
    return cache.get(_cache_key(email))

def _clear_code(email: str) -> None:
    cache.delete(_cache_key(email))

# ===== Views (3 passos) =====
def request_reset_code(request):
    # Passo 1 — recebe o e-mail e envia o código (sem revelar existência)
    if request.method == "POST":
        form = ResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            if User.objects.filter(email__iexact=email).exists():
                code = _gen_code()
                _store_code(email, code, minutes=10)
                send_mail(
                    subject="Seu código de redefinição de senha",
                    message=f"Use este código para redefinir sua senha: {code}\nEle expira em 10 minutos.",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                    recipient_list=[email],
                    fail_silently=False,
                )
            request.session["pwd_reset_email"] = email
            messages.success(request, "Enviamos um código de 6 dígitos para o seu e-mail, se ele existir.")
            # 🔧 namespace 'noticias:'
            return redirect("noticias:password_reset_code")
    else:
        form = ResetEmailForm()
    return render(request, "registration/password_reset_form.html", {"form": form})

def verify_reset_code(request):
    # Passo 2 — valida código de 6 dígitos
    email = request.session.get("pwd_reset_email")
    if not email:
        return redirect("noticias:password_reset")

    bundle = _get_code_bundle(email)

    if request.method == "POST":
        form = CodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if not bundle or timezone.now() > bundle["expires_at"]:
                _clear_code(email)
                messages.error(request, "Código expirado. Peça um novo.")
                return redirect("noticias:password_reset")
            if code != bundle["code"]:
                messages.error(request, "Código inválido. Tente novamente.")
                return render(request, "registration/password_reset_code.html", {"form": form, "email": email})
            request.session["pwd_reset_verified"] = True
            return redirect("noticias:password_reset_new")
    else:
        form = CodeForm()
    return render(request, "registration/password_reset_code.html", {"form": form, "email": email})

def set_new_password(request):
    # Passo 3 — define nova senha
    email = request.session.get("pwd_reset_email")
    verified = request.session.get("pwd_reset_verified")
    if not (email and verified):
        return redirect("noticias:password_reset")

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return redirect("noticias:password_reset")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            _clear_code(email)
            request.session.pop("pwd_reset_email", None)
            request.session.pop("pwd_reset_verified", None)
            messages.success(request, "Senha redefinida com sucesso. Faça login.")
            return redirect("login")
    else:
        form = SetPasswordForm(user)

    return render(request, "registration/password_reset_new.html", {"form": form, "email": email})
