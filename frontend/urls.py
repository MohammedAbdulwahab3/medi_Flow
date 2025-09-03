from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/pharmacist/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('dashboard/manufacturer/', views.manufacturer_dashboard, name='manufacturer_dashboard'),
    
    # Patient catalog
    path('catalog/', views.medicine_catalog, name='medicine_catalog'),
    path('catalog/medicine/<int:medicine_id>/', views.medicine_availability, name='medicine_availability'),
    path('catalog/medicine/<int:medicine_id>/trace/', views.medicine_trace, name='medicine_trace'),
    
    # Pharmacist location settings
    path('pharmacist/settings/location/', views.pharmacist_location_settings, name='pharmacist_location_settings'),
    path('pharmacist/inventory/', views.pharmacist_inventory, name='pharmacist_inventory'),
    path('pharmacist/transfers/', views.pharmacist_transfers, name='pharmacist_transfers'),
    path('pharmacist/transfers/<int:transfer_id>/accept/', views.accept_transfer, name='accept_transfer'),
    
    # Manufacturer Dashboard URLs
    path('manufacturer/medicines/', views.medicine_list, name='medicine_list'),
    path('manufacturer/medicines/<int:medicine_id>/', views.medicine_detail, name='medicine_detail'),
    path('manufacturer/batches/', views.batch_list, name='batch_list'),
    path('manufacturer/inventory/', views.inventory_management, name='inventory_management'),
    path('manufacturer/transfer/', views.transfer_medicine, name='transfer_medicine'),
]
