from django.urls import path
from . import views

app_name = 'prescription'

urlpatterns = [
    path('doctor/create/', views.doctor_create_prescription, name='doctor_create'),
    path('doctor/list/', views.doctor_prescription_list, name='doctor_list'),
    path('doctor/trace/<int:pk>/', views.doctor_trace_prescription, name='doctor_trace'),
    path('doctor/patient-history/', views.doctor_patient_history_lookup, name='doctor_patient_history'),
    path('pharmacist/queue/', views.pharmacist_queue, name='pharmacist_queue'),
    path('pharmacist/dispense/<int:pk>/', views.pharmacist_dispense, name='pharmacist_dispense'),
    path('patient/mine/', views.patient_my_prescriptions, name='patient_mine'),
    path('patient/history/', views.patient_history, name='patient_history'),
    path('patient/trace/<int:pk>/', views.patient_trace_prescription, name='patient_trace'),
]
