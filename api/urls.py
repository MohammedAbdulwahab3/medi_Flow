from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ObtainTokenPairView, PatientProfileView, MedicalRecordView, PrescriptionListView, PrescriptionDetailView, MedicineDetailView, MedicineListView, MedicineAvailabilityView

app_name = 'api'

urlpatterns = [
    path('token/', ObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('patient/me/', PatientProfileView.as_view(), name='patient-me'),
    path('patient/me/medical-record/', MedicalRecordView.as_view(), name='patient-medical-record'),

    path('patient/prescriptions/', PrescriptionListView.as_view(), name='patient-prescriptions'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('medicines/', MedicineListView.as_view(), name='medicine-list'),
    path('medicine/<int:pk>/', MedicineDetailView.as_view(), name='medicine-detail'),
    path('medicine/<int:pk>/availability/', MedicineAvailabilityView.as_view(), name='medicine-availability'),
]
