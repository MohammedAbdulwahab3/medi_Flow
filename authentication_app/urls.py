from django.urls import path
from .views import CustomLoginView, CustomLogoutView, PatientSignUpView, AdminCreateUserView

app_name = 'authentication'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', PatientSignUpView.as_view(), name='signup'),
    path('admin-create-user/', AdminCreateUserView.as_view(), name='admin_create_user'),
]
