from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class LicenseOrUsernameModelBackend(ModelBackend):
    """
    Authenticate using either username OR license_number (plus password).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        # Try username first
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Fall back to license_number lookup
            try:
                user = User.objects.get(license_number=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None
