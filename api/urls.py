from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ObtainTokenPairView, PatientProfileView, MedicalRecordView, PrescriptionListView, PrescriptionDetailView, MedicineDetailView, MedicineListView, MedicineAvailabilityView
from .extra_views import AssignedDoctorsView, NotificationListView, MessageListView, UnreadCountsView, NotificationReadView, NotificationReadAllView
from .analytics_views import RoleBasedAnalyticsView, role_based_advanced_search

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
    
    # Role-based analytics and search
    path('analytics/', RoleBasedAnalyticsView.as_view(), name='role-based-analytics'),
    path('search/', role_based_advanced_search, name='role-based-search'),
    path('patient/assigned-doctors/', AssignedDoctorsView.as_view(), name='assigned-doctors'),
    
    # Notifications and Messages
    path('patient/notifications/', NotificationListView.as_view(), name='patient-notifications'),
    path('patient/notifications/<int:notification_id>/read/', NotificationReadView.as_view(), name='notification-read'),
    path('patient/notifications/read-all/', NotificationReadAllView.as_view(), name='notifications-read-all'),
    path('patient/messages/', MessageListView.as_view(), name='patient-messages'),
    path('patient/unread-counts/', UnreadCountsView.as_view(), name='patient-unread-counts'),
]
