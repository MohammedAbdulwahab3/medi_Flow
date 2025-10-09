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
    
    # Doctor Profile
    path('doctor/profile/edit/', views.doctor_profile_edit, name='doctor_profile_edit'),
    
    # Messaging
    path('messages/', views.message_inbox, name='message_inbox'),
    path('messages/compose/', views.message_compose, name='message_compose'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('api/unread-counts/', views.get_unread_counts, name='get_unread_counts'),
    
    # Doctor-Patient Assignment
    path('doctor/assign-patients/', views.assign_doctor_to_patient, name='assign_doctor_to_patient'),
]
