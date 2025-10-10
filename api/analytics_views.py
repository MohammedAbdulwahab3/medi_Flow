from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import date, timedelta
import json

from rest_framework import generics, permissions
from rest_framework.response import Response

from authentication_app.models import User
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, MedicineTransfer, Sale, SaleItem
from prescription.models import Prescription, Notification, Message


class RoleBasedAnalyticsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Role-based analytics API endpoint
        Returns different analytics data based on user role
        """
        user = request.user
        analytics_data = {}
        
        try:
            if user.is_patient:
                # Patient Analytics
                analytics_data = get_patient_analytics(user)
                
            elif user.is_doctor:
                # Doctor Analytics
                analytics_data = get_doctor_analytics(user)
                
            elif user.is_pharmacist:
                # Pharmacist Analytics
                analytics_data = get_pharmacist_analytics(user)
                
            elif user.is_manufacturer:
                # Manufacturer Analytics
                analytics_data = get_manufacturer_analytics(user)
                
            else:
                return Response({
                    'error': 'Invalid user role',
                    'analytics_data': {}
                }, status=400)
            
            return Response({
                'success': True,
                'analytics_data': analytics_data,
                'user_role': user.role,
                'user_name': user.full_name or user.username
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch analytics: {str(e)}',
                'analytics_data': {}
            }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def role_based_advanced_search(request):
    """
    Role-based advanced search API endpoint
    Returns different search results based on user role and permissions
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        search_type = data.get('type', 'all')
        category = data.get('category', 'all')
        
        if not query:
            return JsonResponse({
                'error': 'Search query is required',
                'results': []
            }, status=400)
        
        user = request.user
        results = {}
        
        if user.is_patient:
            # Patient Search - Limited to medicines and their own prescriptions
            results = get_patient_search_results(user, query, search_type, category)
            
        elif user.is_doctor:
            # Doctor Search - Medicines, patients, prescriptions
            results = get_doctor_search_results(user, query, search_type, category)
            
        elif user.is_pharmacist:
            # Pharmacist Search - Medicines, patients, doctors, prescriptions
            results = get_pharmacist_search_results(user, query, search_type, category)
            
        elif user.is_manufacturer:
            # Manufacturer Search - Medicines, batches, inventory, pharmacists
            results = get_manufacturer_search_results(user, query, search_type, category)
            
        else:
            return JsonResponse({
                'error': 'Invalid user role',
                'results': []
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'query': query,
            'search_type': search_type,
            'category': category,
            'user_role': user.role
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'results': []
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Search failed: {str(e)}',
            'results': []
        }, status=500)


def get_patient_analytics(user):
    """Get analytics data for patients"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Prescription statistics
    prescriptions = Prescription.objects.filter(patient=user)
    recent_prescriptions = prescriptions.filter(prescribed_date__gte=last_30_days)
    
    # Notification statistics
    notifications = Notification.objects.filter(user=user)
    unread_notifications = notifications.filter(is_read=False)
    
    # Message statistics
    messages = Message.objects.filter(
        Q(sender=user) | Q(recipient=user)
    )
    unread_messages = messages.filter(
        recipient=user, is_read=False
    )
    
    analytics = {
        'prescriptions': {
            'total': prescriptions.count(),
            'recent_30_days': recent_prescriptions.count(),
            'pending': prescriptions.filter(status='pending').count(),
            'dispensed': prescriptions.filter(status='dispensed').count(),
            'cancelled': prescriptions.filter(status='cancelled').count(),
        },
        'notifications': {
            'total': notifications.count(),
            'unread': unread_notifications.count(),
            'recent_30_days': notifications.filter(created_at__gte=last_30_days).count(),
        },
        'messages': {
            'total': messages.count(),
            'unread': unread_messages.count(),
            'sent': messages.filter(sender=user).count(),
            'received': messages.filter(recipient=user).count(),
        },
        'medicines': {
            'total_prescribed': prescriptions.values('medicine').distinct().count(),
            'most_prescribed': prescriptions.values('medicine__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5],
        }
    }
    
    return analytics


def get_doctor_analytics(user):
    """Get analytics data for doctors"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Prescription statistics
    prescriptions = Prescription.objects.filter(doctor=user)
    recent_prescriptions = prescriptions.filter(prescribed_date__gte=last_30_days)
    
    # Patient statistics
    patients = User.objects.filter(
        prescriptions__doctor=user
    ).distinct()
    
    # Medicine statistics
    medicines_prescribed = prescriptions.values('medicine').distinct()
    
    analytics = {
        'prescriptions': {
            'total': prescriptions.count(),
            'recent_30_days': recent_prescriptions.count(),
            'pending': prescriptions.filter(status='pending').count(),
            'dispensed': prescriptions.filter(status='dispensed').count(),
            'cancelled': prescriptions.filter(status='cancelled').count(),
        },
        'patients': {
            'total': patients.count(),
            'active': patients.filter(
                prescriptions__prescribed_date__gte=last_30_days
            ).distinct().count(),
        },
        'medicines': {
            'total_prescribed': medicines_prescribed.count(),
            'most_prescribed': prescriptions.values('medicine__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5],
        },
        'recent_activity': {
            'prescriptions_today': prescriptions.filter(
                prescribed_date=today
            ).count(),
            'prescriptions_this_week': prescriptions.filter(
                prescribed_date__gte=today - timedelta(days=7)
            ).count(),
        }
    }
    
    return analytics


def get_pharmacist_analytics(user):
    """Get analytics data for pharmacists"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Sales statistics
    sales = Sale.objects.filter(pharmacist=user)
    recent_sales = sales.filter(sale_date__gte=last_30_days)
    
    # Inventory statistics
    inventory = Inventory.objects.filter(pharmacist=user)
    
    # Prescription statistics (dispensed by this pharmacist)
    prescriptions = Prescription.objects.filter(
        status='dispensed',
        dispensed_by=user
    )
    
    analytics = {
        'sales': {
            'total_revenue': recent_sales.aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
            'total_transactions': recent_sales.count(),
            'average_transaction': recent_sales.aggregate(
                avg=Avg('total_amount')
            )['avg'] or 0,
            'today_revenue': sales.filter(sale_date=today).aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
        },
        'inventory': {
            'total_items': inventory.count(),
            'low_stock': inventory.filter(current_stock__lt=F('minimum_stock')).count(),
            'out_of_stock': inventory.filter(current_stock=0).count(),
            'total_value': inventory.aggregate(
                total=Sum(F('current_stock') * F('batch__medicine__price'))
            )['total'] or 0,
        },
        'prescriptions': {
            'total_dispensed': prescriptions.count(),
            'recent_30_days': prescriptions.filter(
                dispensed_date__gte=last_30_days
            ).count(),
        },
        'top_medicines': SaleItem.objects.filter(
            sale__pharmacist=user,
            sale__sale_date__gte=last_30_days
        ).values('batch__medicine__name').annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('subtotal')
        ).order_by('-total_sold')[:5],
    }
    
    return analytics


def get_manufacturer_analytics(user):
    """Get analytics data for manufacturers"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Medicine statistics
    medicines = Medicine.objects.filter(manufacturer=user)
    batches = MedicineBatch.objects.filter(medicine__manufacturer=user)
    recent_batches = batches.filter(manufacture_date__gte=last_30_days)
    
    # Inventory statistics
    inventory = Inventory.objects.filter(
        batch__medicine__manufacturer=user
    )
    
    # Transfer statistics
    transfers = MedicineTransfer.objects.filter(from_user=user)
    recent_transfers = transfers.filter(transfer_date__gte=last_30_days)
    
    analytics = {
        'medicines': {
            'total': medicines.count(),
            'active': medicines.filter(is_active=True).count(),
            'categories': medicines.values('category').annotate(
                count=Count('id')
            ).order_by('-count'),
        },
        'batches': {
            'total': batches.count(),
            'recent_30_days': recent_batches.count(),
            'expiring_soon': batches.filter(
                expiry_date__lte=today + timedelta(days=30)
            ).count(),
        },
        'inventory': {
            'total_stock': inventory.aggregate(
                total=Sum('current_stock')
            )['total'] or 0,
            'total_value': inventory.aggregate(
                total=Sum(F('current_stock') * F('batch__medicine__price'))
            )['total'] or 0,
            'low_stock_items': inventory.filter(
                current_stock__lt=F('minimum_stock')
            ).count(),
        },
        'transfers': {
            'total': transfers.count(),
            'recent_30_days': recent_transfers.count(),
            'pending': transfers.filter(status='pending').count(),
            'completed': transfers.filter(status='completed').count(),
        },
        'top_medicines': medicines.annotate(
            total_batches=Count('medicinebatch'),
            total_inventory=Sum('medicinebatch__inventory__current_stock')
        ).order_by('-total_inventory')[:5],
    }
    
    return analytics


def get_patient_search_results(user, query, search_type, category):
    """Get search results for patients"""
    results = {}
    
    if search_type in ['all', 'medicines']:
        # Search medicines
        medicines_query = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(description__icontains=query)
        )
        
        if category != 'all':
            medicines_query = medicines_query.filter(category=category)
        
        medicines = medicines_query.select_related('manufacturer')[:10]
        results['medicines'] = [
            {
                'id': med.id,
                'name': med.name,
                'generic_name': med.generic_name,
                'category': med.category,
                'description': med.description,
                'manufacturer': med.manufacturer.full_name if med.manufacturer else 'Unknown',
                'type': 'medicine'
            }
            for med in medicines
        ]
    
    if search_type in ['all', 'prescriptions']:
        # Search own prescriptions
        prescriptions = Prescription.objects.filter(
            Q(medicine__name__icontains=query) |
            Q(doctor__username__icontains=query) |
            Q(notes__icontains=query),
            patient=user
        ).select_related('doctor', 'medicine').order_by('-prescribed_date')[:10]
        
        results['prescriptions'] = [
            {
                'id': pres.id,
                'medicine_name': pres.medicine.name,
                'doctor_name': pres.doctor.full_name or pres.doctor.username,
                'status': pres.status,
                'prescribed_date': pres.prescribed_date.isoformat(),
                'dosage': pres.dosage,
                'type': 'prescription'
            }
            for pres in prescriptions
        ]
    
    return results


def get_doctor_search_results(user, query, search_type, category):
    """Get search results for doctors"""
    results = {}
    
    if search_type in ['all', 'medicines']:
        # Search medicines
        medicines_query = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(description__icontains=query)
        )
        
        if category != 'all':
            medicines_query = medicines_query.filter(category=category)
        
        medicines = medicines_query.select_related('manufacturer')[:10]
        results['medicines'] = [
            {
                'id': med.id,
                'name': med.name,
                'generic_name': med.generic_name,
                'category': med.category,
                'description': med.description,
                'manufacturer': med.manufacturer.full_name if med.manufacturer else 'Unknown',
                'type': 'medicine'
            }
            for med in medicines
        ]
    
    if search_type in ['all', 'patients']:
        # Search patients (assigned to this doctor)
        patients = User.objects.filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query),
            prescriptions__doctor=user
        ).distinct()[:10]
        
        results['patients'] = [
            {
                'id': patient.id,
                'username': patient.username,
                'full_name': patient.full_name,
                'email': patient.email,
                'phone': patient.phone,
                'type': 'patient'
            }
            for patient in patients
        ]
    
    if search_type in ['all', 'prescriptions']:
        # Search prescriptions
        prescriptions = Prescription.objects.filter(
            Q(medicine__name__icontains=query) |
            Q(patient__username__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(notes__icontains=query),
            doctor=user
        ).select_related('patient', 'medicine').order_by('-prescribed_date')[:10]
        
        results['prescriptions'] = [
            {
                'id': pres.id,
                'medicine_name': pres.medicine.name,
                'patient_name': pres.patient.full_name or pres.patient.username,
                'status': pres.status,
                'prescribed_date': pres.prescribed_date.isoformat(),
                'dosage': pres.dosage,
                'type': 'prescription'
            }
            for pres in prescriptions
        ]
    
    return results


def get_pharmacist_search_results(user, query, search_type, category):
    """Get search results for pharmacists"""
    results = {}
    
    if search_type in ['all', 'medicines']:
        # Search medicines
        medicines_query = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(description__icontains=query)
        )
        
        if category != 'all':
            medicines_query = medicines_query.filter(category=category)
        
        medicines = medicines_query.select_related('manufacturer')[:10]
        results['medicines'] = [
            {
                'id': med.id,
                'name': med.name,
                'generic_name': med.generic_name,
                'category': med.category,
                'description': med.description,
                'manufacturer': med.manufacturer.full_name if med.manufacturer else 'Unknown',
                'type': 'medicine'
            }
            for med in medicines
        ]
    
    if search_type in ['all', 'patients']:
        # Search patients
        patients = User.objects.filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query),
            role=User.ROLE_PATIENT
        )[:10]
        
        results['patients'] = [
            {
                'id': patient.id,
                'username': patient.username,
                'full_name': patient.full_name,
                'email': patient.email,
                'phone': patient.phone,
                'type': 'patient'
            }
            for patient in patients
        ]
    
    if search_type in ['all', 'doctors']:
        # Search doctors
        doctors = User.objects.filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query),
            role=User.ROLE_DOCTOR
        )[:10]
        
        results['doctors'] = [
            {
                'id': doctor.id,
                'username': doctor.username,
                'full_name': doctor.full_name,
                'email': doctor.email,
                'license_number': doctor.license_number,
                'type': 'doctor'
            }
            for doctor in doctors
        ]
    
    if search_type in ['all', 'prescriptions']:
        # Search prescriptions
        prescriptions = Prescription.objects.filter(
            Q(medicine__name__icontains=query) |
            Q(patient__username__icontains=query) |
            Q(patient__full_name__icontains=query) |
            Q(doctor__username__icontains=query) |
            Q(notes__icontains=query)
        ).select_related('patient', 'doctor', 'medicine').order_by('-prescribed_date')[:10]
        
        results['prescriptions'] = [
            {
                'id': pres.id,
                'medicine_name': pres.medicine.name,
                'patient_name': pres.patient.full_name or pres.patient.username,
                'doctor_name': pres.doctor.full_name or pres.doctor.username,
                'status': pres.status,
                'prescribed_date': pres.prescribed_date.isoformat(),
                'dosage': pres.dosage,
                'type': 'prescription'
            }
            for pres in prescriptions
        ]
    
    return results


def get_manufacturer_search_results(user, query, search_type, category):
    """Get search results for manufacturers"""
    results = {}
    
    if search_type in ['all', 'medicines']:
        # Search own medicines
        medicines_query = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(description__icontains=query),
            manufacturer=user
        )
        
        if category != 'all':
            medicines_query = medicines_query.filter(category=category)
        
        medicines = medicines_query[:10]
        results['medicines'] = [
            {
                'id': med.id,
                'name': med.name,
                'generic_name': med.generic_name,
                'category': med.category,
                'description': med.description,
                'is_active': med.is_active,
                'type': 'medicine'
            }
            for med in medicines
        ]
    
    if search_type in ['all', 'batches']:
        # Search batches
        batches = MedicineBatch.objects.filter(
            Q(batch_number__icontains=query) |
            Q(medicine__name__icontains=query),
            medicine__manufacturer=user
        ).select_related('medicine').order_by('-manufacture_date')[:10]
        
        results['batches'] = [
            {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'medicine_name': batch.medicine.name,
                'manufacture_date': batch.manufacture_date.isoformat(),
                'expiry_date': batch.expiry_date.isoformat(),
                'quantity': batch.quantity,
                'type': 'batch'
            }
            for batch in batches
        ]
    
    if search_type in ['all', 'pharmacists']:
        # Search pharmacists
        pharmacists = User.objects.filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query) |
            Q(email__icontains=query),
            role=User.ROLE_PHARMACIST
        )[:10]
        
        results['pharmacists'] = [
            {
                'id': pharmacist.id,
                'username': pharmacist.username,
                'full_name': pharmacist.full_name,
                'email': pharmacist.email,
                'license_number': pharmacist.license_number,
                'type': 'pharmacist'
            }
            for pharmacist in pharmacists
        ]
    
    if search_type in ['all', 'inventory']:
        # Search inventory
        inventory = Inventory.objects.filter(
            Q(batch__medicine__name__icontains=query) |
            Q(batch__batch_number__icontains=query),
            batch__medicine__manufacturer=user
        ).select_related('batch__medicine', 'pharmacist').order_by('-id')[:10]
        
        results['inventory'] = [
            {
                'id': inv.id,
                'medicine_name': inv.batch.medicine.name,
                'batch_number': inv.batch.batch_number,
                'pharmacist_name': inv.pharmacist.full_name or inv.pharmacist.username,
                'current_stock': inv.current_stock,
                'minimum_stock': inv.minimum_stock,
                'type': 'inventory'
            }
            for inv in inventory
        ]
    
    return results
