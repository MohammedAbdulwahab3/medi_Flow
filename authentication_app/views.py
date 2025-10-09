# authentication_app/views.py
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth import get_user_model

from .forms import PatientSignUpForm, AdminUserCreateForm

User = get_user_model()

class RoleRedirectMixin:
    def get_redirect_for_user(self, user):
        if user.role == User.ROLE_DOCTOR:
            return reverse_lazy('frontend:doctor_dashboard')
        if user.role == User.ROLE_PHARMACIST:
            return reverse_lazy('frontend:pharmacist_dashboard')
        if user.role == User.ROLE_MANUFACTURER:
            return reverse_lazy('frontend:manufacturer_dashboard')
        if user.role == User.ROLE_PATIENT:
            return reverse_lazy('frontend:patient_dashboard')
        return reverse_lazy('admin:index')


class CustomLoginView(LoginView, RoleRedirectMixin):
    template_name = 'authentication/login.html'

    def get_success_url(self):
        return self.get_redirect_for_user(self.request.user)


class CustomLogoutView(LogoutView):
    template_name = 'authentication/logout.html'


class PatientSignUpView(CreateView):
    template_name = 'authentication/signup.html'
    form_class = PatientSignUpForm

    def form_valid(self, form):
        # 1) create the user
        created_user = form.save()

        # 2) try to authenticate (this will attach a backend to the returned user)
        raw_password = form.cleaned_data.get('password1')
        auth_user = authenticate(self.request, username=created_user.username, password=raw_password)

        if auth_user is not None:
            # authenticate returned a user with backend attribute set — safe to login without specifying backend
            login(self.request, auth_user)
            return redirect(self.get_redirect_for_user(auth_user))

        # Fallback: if authenticate failed for some reason, supply a backend explicitly.
        # Use the first backend listed in settings (adjust if you want a different one).
        backend_path = settings.AUTHENTICATION_BACKENDS[0]
        login(self.request, created_user, backend=backend_path)
        return redirect(self.get_redirect_for_user(created_user))


@method_decorator(staff_member_required, name='dispatch')
class AdminCreateUserView(CreateView):
    template_name = 'authentication/admin_create_user.html'
    form_class = AdminUserCreateForm
    success_url = reverse_lazy('authentication:admin_create_user')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
