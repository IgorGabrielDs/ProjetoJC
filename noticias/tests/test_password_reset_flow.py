import re
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache

User = get_user_model()

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetByCodeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="OldPass#123"
        )

    def _extract_code_from_outbox(self):
        self.assertTrue(mail.outbox, "Nenhum e-mail foi enviado.")
        body = mail.outbox[-1].body
        m = re.search(r"\b(\d{6})\b", body)
        self.assertIsNotNone(m, "Código de 6 dígitos não encontrado no e-mail.")
        return m.group(1)

    def test_fluxo_completo_reseta_senha(self):
        # Passo 1: solicitar código
        resp = self.client.post(reverse("noticias:password_reset"), {"email": "alice@example.com"})
        self.assertRedirects(resp, reverse("noticias:password_reset_code"))

        code = self._extract_code_from_outbox()

        # Passo 2: validar código
        resp = self.client.post(reverse("noticias:password_reset_code"), {"code": code})
        self.assertRedirects(resp, reverse("noticias:password_reset_new"))

        # Passo 3: definir nova senha
        resp = self.client.post(
            reverse("noticias:password_reset_new"),
            {"new_password1": "NewPass#456", "new_password2": "NewPass#456"},
        )
        self.assertRedirects(resp, reverse("login"))

        # Login com a nova senha para confirmar
        login = self.client.post(reverse("login"), {"username": "alice", "password": "NewPass#456"})
        self.assertEqual(login.status_code, 302)

    def test_codigo_invalido(self):
        self.client.post(reverse("noticias:password_reset"), {"email": "alice@example.com"})
        resp = self.client.post(reverse("noticias:password_reset_code"), {"code": "000000"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Código inválido")

    def test_sem_email_na_sessao_redireciona(self):
        resp = self.client.get(reverse("noticias:password_reset_code"))
        self.assertRedirects(resp, reverse("noticias:password_reset"))

    def test_nao_revela_existencia_do_email(self):
        resp = self.client.post(reverse("noticias:password_reset"), {"email": "naoexiste@example.com"}, follow=True)
        self.assertEqual(resp.status_code, 200)  # mensagem genérica
        # Não deve vazar informação — apenas mensagem de “se existir”
        self.assertContains(resp, "código de 6 dígitos")
