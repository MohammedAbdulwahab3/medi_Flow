from django.urls import path
from . import views
from . import pharmacy_views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/pharmacist/', pharmacy_views.enhanced_pharmacist_dashboard, name='pharmacist_dashboard'),
    path('pharmacist/search/', views.pharmacist_medicine_search, name='pharmacist_medicine_search'),
    path('pharmacist/medicine/<int:medicine_id>/detail/', views.pharmacist_medicine_detail, name='pharmacist_medicine_detail'),
    path('dashboard/manufacturer/', views.manufacturer_dashboard, name='manufacturer_dashboard'),
    
    # Patient catalog
    path('catalog/', views.medicine_catalog, name='medicine_catalog'),
    path('catalog/medicine/<int:medicine_id>/', views.medicine_availability, name='medicine_availability'),
    path('catalog/medicine/<int:medicine_id>/detail/', views.medicine_detail_page, name='medicine_detail_page'),
    path('catalog/medicine/<int:medicine_id>/manufacturers/', views.medicine_manufacturers, name='medicine_manufacturers'),
    path('catalog/medicine/<int:medicine_id>/trace/', views.medicine_trace, name='medicine_trace'),
    
    # Pharmacist location settings
    path('pharmacist/settings/location/', views.pharmacist_location_settings, name='pharmacist_location_settings'),
    path('pharmacist/inventory/', views.pharmacist_inventory, name='pharmacist_inventory'),
    path('pharmacist/transfers/', views.pharmacist_transfers, name='pharmacist_transfers'),
    path('pharmacist/transfers/<int:transfer_id>/accept/', views.accept_transfer, name='accept_transfer'),
    
    # Manufacturer Dashboard URLs
    path('manufacturer/medicines/', views.medicine_list, name='medicine_list'),
    path('manufacturer/medicines/<int:medicine_id>/', views.medicine_detail, name='medicine_detail'),
    path('manufacturer/medicines/<int:medicine_id>/simple/', views.medicine_detail_simple, name='medicine_detail_simple'),
    path('manufacturer/medicines/<int:medicine_id>/edit/', views.edit_medicine, name='medicine_edit'),
    path('manufacturer/batches/', views.batch_list, name='batch_list'),
    path('manufacturer/inventory/', views.inventory_management, name='inventory_management'),
    path('manufacturer/inventory/<int:inventory_id>/view/', views.manufacturer_inventory_detail, name='manufacturer_inventory_detail'),
    path('manufacturer/inventory/<int:inventory_id>/accept/', views.manufacturer_accept_reservation, name='manufacturer_accept_reservation'),
    path('manufacturer/reservations/', views.manufacturer_reservation_list, name='manufacturer_reservations'),
    path('manufacturer/reservations/<int:request_id>/<str:action>/', views.respond_reservation_request, name='manufacturer_respond_reservation'),
    path('manufacturer/reservations/<int:reservation_id>/', views.reservation_detail, name='manufacturer_reservation_detail'),
    path('manufacturer/transfer/', views.transfer_medicine, name='transfer_medicine'),
    path('pharmacist/inventory/<int:inventory_id>/request/', views.request_reservation, name='request_reservation'),
    path('pharmacist/reservation/create/', views.create_reservation_request, name='create_reservation_request'),
    path('pharmacist/reservations/', views.pharmacist_reservations, name='pharmacist_reservations'),
    
    # Pharmacy Features
    path('pharmacist/prescriptions/queue/', pharmacy_views.prescription_queue, name='prescription_queue'),
    path('pharmacist/prescriptions/<int:prescription_id>/dispense/', pharmacy_views.dispense_prescription, name='dispense_prescription'),
    path('pharmacist/sales/analytics/', pharmacy_views.sales_analytics, name='sales_analytics'),
    path('pharmacist/sales/export/', pharmacy_views.export_sales_report, name='export_sales_report'),
    path('pharmacist/reorder/', pharmacy_views.reorder_management, name='reorder_management'),
    path('pharmacist/reorder/<int:alert_id>/request/', pharmacy_views.create_reorder_request, name='create_reorder_request'),
    path('pharmacist/reorder/<int:alert_id>/dismiss/', pharmacy_views.dismiss_reorder_alert, name='dismiss_reorder_alert'),
    
    # Modern Features
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('search/', views.advanced_search, name='advanced_search'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('appointments/', views.appointment_scheduler, name='appointment_scheduler'),
    path('emergency/', views.emergency_contacts, name='emergency_contacts'),
    path('bulk/', views.bulk_operations, name='bulk_operations'),
]
