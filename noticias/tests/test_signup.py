from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class SignupTests(TestCase):
    def test_signup_cria_usuario_e_faz_login(self):
        data = {
            "nome": "Maria Teste",
            "email": "maria@example.com",
            "data_nascimento": "2000-01-01",
            "password1": "Senha#Fort3",
            "password2": "Senha#Fort3",
            "terms": "on",
        }
        resp = self.client.post(reverse("noticias:signup"), data, follow=False)
        # Redireciona para home após sucesso (como sua view faz)
        self.assertEqual(resp.status_code, 302)

        # Usuário foi criado
        self.assertTrue(User.objects.filter(email="maria@example.com").exists())

        # E está autenticado (sessão ativa)
        home = self.client.get(reverse("noticias:index"))
        self.assertTrue(home.wsgi_request.user.is_authenticated)

    def test_signup_email_unico(self):
        User.objects.create_user(username="joao@example.com", email="joao@example.com", password="X")
        data = {
            "nome": "João 2",
            "email": "joao@example.com",
            "data_nascimento": "2001-01-01",
            "password1": "Senha#Fort3",
            "password2": "Senha#Fort3",
            "terms": "on",
        }
        resp = self.client.post(reverse("noticias:signup"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Este e-mail já está cadastrado.")

    def test_signup_senhas_diferentes(self):
        data = {
            "nome": "Ana",
            "email": "ana@example.com",
            "data_nascimento": "2002-01-01",
            "password1": "Senha#Fort3",
            "password2": "Senha#Diff",
            "terms": "on",
        }
        resp = self.client.post(reverse("noticias:signup"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "As senhas não coincidem.")

    def test_signup_terms_obrigatorio(self):
        data = {
            "nome": "Pedro",
            "email": "pedro@example.com",
            "data_nascimento": "2003-01-01",
            "password1": "Senha#Fort3",
            "password2": "Senha#Fort3",
            # sem 'terms'
        }
        resp = self.client.post(reverse("noticias:signup"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "É necessário concordar com os Termos de Uso.")
