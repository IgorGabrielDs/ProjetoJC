# noticias/tests/test_login.py
from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class LoginViewTests(TestCase):
    def setUp(self):
        # Usuário de teste (pode logar com username ou email, conforme seu backend)
        self.password = "teste@12345"
        self.user = User.objects.create_user(
            username="user_teste",
            email="user@exemplo.com",
            password=self.password,
        )
        self.url_login = reverse("login")

    def test_pagina_login_carrega_ok(self):
        resp = self.client.get(self.url_login)
        self.assertEqual(resp.status_code, 200)
        # Verifica campos principais
        self.assertContains(resp, 'name="username"')
        self.assertContains(resp, 'name="password"')
        # Verifica título
        self.assertContains(resp, "Entrar — JC")
        # Template padrão do Django Auth (ajuste se você usa outro)
        self.assertTemplateUsed(resp, "registration/login.html")

    def test_pagina_login_inclui_csrf(self):
        resp = self.client.get(self.url_login)
        self.assertContains(resp, "csrfmiddlewaretoken")

    def test_login_sucesso_redireciona_para_next(self):
        next_url = "/salvos/"
        resp = self.client.post(
            self.url_login + f"?next={next_url}",
            {"username": "user@exemplo.com", "password": self.password},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(next_url, resp["Location"])

    def test_login_sucesso_redireciona_para_login_redirect_url(self):
        # Quando não há ?next, deve ir para LOGIN_REDIRECT_URL
        resp = self.client.post(
            self.url_login,
            {"username": "user_teste", "password": self.password},
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        destino = resp["Location"]
        esperado = getattr(settings, "LOGIN_REDIRECT_URL", "/")
        # Pode ser absoluto em alguns setups; por isso só verifica sufixo
        self.assertTrue(destino.endswith(esperado))

    def test_login_invalido_mostra_erro(self):
        resp = self.client.post(
            self.url_login,
            {"username": "user_teste", "password": "senha_errada"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        # Sua página mostra um bloco .errors quando há erro:
        self.assertContains(resp, "Verifique seus dados e tente novamente.")

    def test_hidden_next_renderizado_quando_passado(self):
        next_url = "/noticias/123/"
        resp = self.client.get(self.url_login + f"?next={next_url}")
        self.assertContains(resp, f'name="next" value="{next_url}"')

    def test_link_signup_existe(self):
        # O template usa {% url 'noticias:signup' %}
        try:
            url_signup = reverse("noticias:signup")
        except NoReverseMatch:
            self.fail("A URL nomeada 'noticias:signup' não está configurada.")
        resp = self.client.get(self.url_login)
        self.assertContains(resp, url_signup)

    def test_link_password_reset_existe_se_configurado(self):
        # Caso seu projeto não tenha reset de senha, este teste pode ser ignorado
        try:
            url_reset = reverse("password_reset")
        except NoReverseMatch:
            self.skipTest("URL 'password_reset' não está configurada neste projeto.")
        resp = self.client.get(self.url_login)
        self.assertContains(resp, url_reset)

    def test_icones_providers_renderizam(self):
        resp = self.client.get(self.url_login)
        # Verifica ícones (placeholders) usados no template
        self.assertContains(resp, "icon-google.svg")
        self.assertContains(resp, "icon-apple.svg")
        self.assertContains(resp, "icon-facebook.svg")
    def test_login_nao_cria_usuario_inexistente(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        total_antes = User.objects.count()

        resp = self.client.post(
            self.url_login,
            {"username": "naoexiste@example.com", "password": "Qualquer#123"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)  # volta pro form
        self.assertEqual(User.objects.count(), total_antes)  # ninguém novo criado
