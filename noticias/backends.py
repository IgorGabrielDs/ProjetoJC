from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """Autentica usando e-mail OU username no mesmo campo 'username'."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD) #type: ignore

        if not username or not password:
            return None

        user = (
            User.objects
            .filter(Q(email__iexact=username) | Q(**{User.USERNAME_FIELD: username})) #type: ignore
            .order_by("id")
            .first()
        )
        if not user:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
