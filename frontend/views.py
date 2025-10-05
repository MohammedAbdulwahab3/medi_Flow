from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, F
from django.db import transaction
from django import forms
from datetime import date, timedelta

from authentication_app.models import User
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, MedicineTransfer
from inventory.models import PharmacyInventory
from inventory.models import ReservationRequest
from medicine.forms import MedicineForm, MedicineBatchForm
from inventory.forms import InventoryForm, MedicineTransferForm
from inventory.forms import ReservationRequestForm
from authentication_app.models import PharmacistProfile

def is_manufacturer(user):
    return user.is_authenticated and user.role == User.ROLE_MANUFACTURER


def home(request):
    """Public landing page"""
    return render(request, 'home.html')


@login_required
def patient_dashboard(request):
    from prescription.models import Prescription, PatientDoctorAssignment, Notification
    
    # Get recent prescriptions
    recent_prescriptions = Prescription.objects.filter(
        patient=request.user
    ).select_related('doctor', 'medicine').order_by('-prescribed_date')[:5]
    
    # Get assigned doctors
    assigned_doctors = PatientDoctorAssignment.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__doctor_profile').order_by('-is_primary', '-assigned_date')
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:5]
    
    # Statistics
    total_prescriptions = Prescription.objects.filter(patient=request.user).count()
    pending_prescriptions = Prescription.objects.filter(patient=request.user, status='pending').count()
    dispensed_prescriptions = Prescription.objects.filter(patient=request.user, status='dispensed').count()
    
    context = {
        'recent_prescriptions': recent_prescriptions,
        'assigned_doctors': assigned_doctors,
        'unread_notifications': unread_notifications,
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'dispensed_prescriptions': dispensed_prescriptions,
    }
    
    return render(request, 'frontend/patient/patient_dashboard.html', context)


@login_required
def doctor_dashboard(request):
    from prescription.models import Prescription, PatientDoctorAssignment, DoctorProfile, Notification
    from django.db.models import Count
    
    # Get or create doctor profile
    doctor_profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
    
    # Get assigned patients
    assigned_patients = PatientDoctorAssignment.objects.filter(
        doctor=request.user
    ).select_related('patient').order_by('-is_primary', '-assigned_date')[:10]
    
    # Get recent prescriptions
    recent_prescriptions = Prescription.objects.filter(
        doctor=request.user
    ).select_related('patient', 'medicine').order_by('-prescribed_date')[:10]
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=request.user, is_read=False
    ).order_by('-created_at')[:5]
    
    # Statistics
    total_patients = PatientDoctorAssignment.objects.filter(doctor=request.user).count()
    total_prescriptions = Prescription.objects.filter(doctor=request.user).count()
    pending_prescriptions = Prescription.objects.filter(doctor=request.user, status='pending').count()
    dispensed_prescriptions = Prescription.objects.filter(doctor=request.user, status='dispensed').count()
    
    context = {
        'doctor_profile': doctor_profile,
        'assigned_patients': assigned_patients,
        'recent_prescriptions': recent_prescriptions,
        'unread_notifications': unread_notifications,
        'total_patients': total_patients,
        'total_prescriptions': total_prescriptions,
        'pending_prescriptions': pending_prescriptions,
        'dispensed_prescriptions': dispensed_prescriptions,
    }
    
    return render(request, 'frontend/doctor/doctor_dashboard.html', context)


@login_required
def pharmacist_dashboard(request):
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q
    
    user = request.user
    if not user.is_pharmacist:
        return redirect('frontend:home')
    
    # Get today and date ranges
    today = date.today()
    thirty_days = today + timedelta(days=30)
    seven_days = today + timedelta(days=7)
    
    # === INVENTORY STATISTICS ===
    my_inventory = PharmacyInventory.objects.filter(pharmacist=user).select_related('batch__medicine')
    total_items = my_inventory.count()
    total_stock = my_inventory.aggregate(total=Sum('current_stock'))['total'] or 0
    
    # Low stock items (less than 10 units)
    low_stock_items = my_inventory.filter(current_stock__lt=10).order_by('current_stock')[:10]
    low_stock_count = my_inventory.filter(current_stock__lt=10).count()
    
    # Expiring items
    expiring_soon = my_inventory.filter(
        batch__expiry_date__lte=thirty_days,
        batch__expiry_date__gt=today
    ).order_by('batch__expiry_date')[:10]
    expiring_count = my_inventory.filter(
        batch__expiry_date__lte=thirty_days,
        batch__expiry_date__gt=today
    ).count()
    
    # Expired items
    expired_items = my_inventory.filter(batch__expiry_date__lte=today)
    expired_count = expired_items.count()
    
    # Critical alerts (expiring in 7 days)
    critical_items = my_inventory.filter(
        batch__expiry_date__lte=seven_days,
        batch__expiry_date__gt=today
    ).order_by('batch__expiry_date')[:5]
    critical_count = critical_items.count()
    
    # === INCOMING TRANSFERS ===
    incoming_transfers = MedicineTransfer.objects.filter(
        to_user=user, 
        is_completed=False
    ).select_related('from_user', 'batch__medicine').order_by('-transfer_date')[:5]
    pending_transfers_count = MedicineTransfer.objects.filter(
        to_user=user, 
        is_completed=False
    ).count()
    
    # === RESERVATION REQUESTS ===
    my_requests = ReservationRequest.objects.filter(
        pharmacy=user
    ).order_by('-created_at')[:5]
    pending_requests_count = ReservationRequest.objects.filter(
        pharmacy=user,
        status=ReservationRequest.STATUS_PENDING
    ).count()
    
    # === PRESCRIPTION STATS (if prescription app exists) ===
    try:
        from prescription.models import Prescription
        pending_prescriptions = Prescription.objects.filter(
            status='pending'
        ).select_related('patient', 'medicine')[:5]
        pending_prescriptions_count = Prescription.objects.filter(status='pending').count()
    except:
        pending_prescriptions = []
        pending_prescriptions_count = 0
    
    # === VALUE OF INVENTORY ===
    inventory_value = 0
    for inv in my_inventory:
        price = inv.get_price() if inv.selling_price else (inv.batch.selling_price if inv.batch else 0)
        inventory_value += float(price or 0) * inv.current_stock
    
    context = {
        # Statistics
        'total_items': total_items,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
        'critical_count': critical_count,
        'pending_transfers_count': pending_transfers_count,
        'pending_requests_count': pending_requests_count,
        'pending_prescriptions_count': pending_prescriptions_count,
        'inventory_value': round(inventory_value, 2),
        
        # Data lists
        'low_stock_items': low_stock_items,
        'expiring_soon': expiring_soon,
        'expired_items': expired_items,
        'critical_items': critical_items,
        'incoming_transfers': incoming_transfers,
        'my_requests': my_requests,
        'pending_prescriptions': pending_prescriptions,
    }
    
    return render(request, 'frontend/pharmacist/pharmacist_dashboard.html', context)


@login_required
def pharmacist_medicine_search(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')

    q = (request.GET.get('q') or '').strip()
    medicines = Medicine.objects.filter(is_active=True).select_related('manufacturer').order_by('name')
    
    # Apply search filter if query provided
    if q:
        from django.db.models import Q
        medicines = medicines.filter(Q(name__icontains=q) | Q(generic_name__icontains=q))
    else:
        # If no search, limit to first 20 medicines to avoid loading too many
        medicines = medicines[:20]

    # For each medicine compute total available across all manufacturers and price range
    from django.db.models import Sum, F, Min, Max
    med_list = []
    for med in medicines:
        # Calculate available stock from manufacturer inventory
        total_available = (Inventory.objects.filter(
            batch__medicine=med
        ).annotate(
            available=F('current_stock') - F('reserved_stock')
        ).aggregate(total=Sum('available'))['total']) or 0
        
        # Get price range from manufacturer batches (cost price)
        price_data = MedicineBatch.objects.filter(
            medicine=med, 
            is_active=True
        ).aggregate(
            min_price=Min('cost_price'),
            max_price=Max('cost_price')
        )
        
        med_list.append({
            'medicine': med, 
            'available': total_available,
            'min_price': price_data.get('min_price'),
            'max_price': price_data.get('max_price'),
        })

    return render(request, 'frontend/pharmacist/medicine_search.html', {'med_rows': med_list, 'q': q})


@login_required
def pharmacist_medicine_detail(request, medicine_id):
    """Pharmacist-specific medicine detail page showing manufacturer info and ordering options"""
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    
    # Get manufacturer inventory (available stock from manufacturer)
    from django.db.models import Sum, F, Min, Max
    total_available = (Inventory.objects.filter(
        batch__medicine=medicine
    ).annotate(
        available=F('current_stock') - F('reserved_stock')
    ).aggregate(total=Sum('available'))['total']) or 0
    
    # Get all batches from manufacturer
    batches = MedicineBatch.objects.filter(
        medicine=medicine,
        is_active=True
    ).select_related('medicine__manufacturer').order_by('-manufacturing_date')
    
    # Get price range
    price_data = batches.aggregate(
        min_price=Min('cost_price'),
        max_price=Max('cost_price')
    )
    
    # Get manufacturer inventory details
    manufacturer_inventory = Inventory.objects.filter(
        batch__medicine=medicine
    ).select_related('batch').annotate(
        available=F('current_stock') - F('reserved_stock')
    )
    
    # Check if pharmacist already has this medicine
    pharmacist_stock = PharmacyInventory.objects.filter(
        pharmacist=request.user,
        batch__medicine=medicine
    ).select_related('batch').aggregate(
        total=Sum('current_stock')
    )['total'] or 0
    
    # Get existing reservation requests for this medicine
    existing_requests = ReservationRequest.objects.filter(
        pharmacy=request.user,
        medicine=medicine
    ).select_related('manufacturer').order_by('-created_at')[:5]
    
    context = {
        'medicine': medicine,
        'total_available': total_available,
        'min_price': price_data.get('min_price'),
        'max_price': price_data.get('max_price'),
        'batches': batches,
        'manufacturer_inventory': manufacturer_inventory,
        'pharmacist_stock': pharmacist_stock,
        'existing_requests': existing_requests,
    }
    
    return render(request, 'frontend/pharmacist/medicine_detail.html', context)


# Patient catalog views
@login_required
def medicine_catalog(request):
    q = (request.GET.get('q') or '').strip()
    category = request.GET.get('category', '')
    
    medicines = Medicine.objects.filter(is_active=True).select_related('manufacturer')
    
    if q:
        from django.db.models import Q
        medicines = medicines.filter(
            Q(name__icontains=q) | 
            Q(generic_name__icontains=q) | 
            Q(description__icontains=q)
        )
    
    if category:
        medicines = medicines.filter(category=category)
    
    # Get price range and availability for each medicine
    med_list = []
    for med in medicines.order_by('name'):
        price_range = med.get_price_range()
        # Check total availability across all pharmacies
        total_available = PharmacyInventory.objects.filter(
            batch__medicine=med, 
            current_stock__gt=0
        ).aggregate(total=Sum('current_stock'))['total'] or 0
        
        med_list.append({
            'medicine': med,
            'min_price': price_range.get('min_price'),
            'max_price': price_range.get('max_price'),
            'available_stock': total_available,
        })
    
    # Get all categories for filter
    categories = Medicine.CATEGORY_CHOICES
    
    return render(request, 'frontend/patient/catalog.html', {
        'med_list': med_list, 
        'q': q,
        'category': category,
        'categories': categories,
    })


@login_required
def medicine_availability(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    
    # Get all pharmacies with stock, group by pharmacist with total stock and best price
    inventories = PharmacyInventory.objects.filter(
        batch__medicine=medicine, 
        current_stock__gt=0
    ).select_related('pharmacist__pharmacist_profile', 'batch__medicine')
    
    # Group by pharmacy and calculate totals
    pharmacy_data = {}
    for inv in inventories:
        pharm_id = inv.pharmacist.id
        if pharm_id not in pharmacy_data:
            pharmacy_data[pharm_id] = {
                'pharmacist': inv.pharmacist,
                'profile': getattr(inv.pharmacist, 'pharmacist_profile', None),
                'total_stock': 0,
                'prices': [],
                'batches': [],
            }
        
        pharmacy_data[pharm_id]['total_stock'] += inv.current_stock
        price = inv.get_price()
        if price:
            pharmacy_data[pharm_id]['prices'].append(float(price))
        pharmacy_data[pharm_id]['batches'].append({
            'batch': inv.batch,
            'stock': inv.current_stock,
            'price': price,
        })
    
    # Calculate min price for each pharmacy
    pharmacy_list = []
    for data in pharmacy_data.values():
        data['min_price'] = min(data['prices']) if data['prices'] else None
        data['max_price'] = max(data['prices']) if data['prices'] else None
        pharmacy_list.append(data)
    
    # Sort by price (lowest first)
    pharmacy_list.sort(key=lambda x: x['min_price'] if x['min_price'] else float('inf'))
    
    # Get all batches for trace functionality
    all_batches = medicine.batches.filter(is_active=True).select_related('medicine__manufacturer')
    
    return render(request, 'frontend/patient/medicine_availability.html', {
        'medicine': medicine,
        'pharmacy_list': pharmacy_list,
        'all_batches': all_batches,
        'total_pharmacies': len(pharmacy_list),
    })


@login_required
def medicine_detail_page(request, medicine_id):
    """Comprehensive medicine detail page with all information"""
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    
    # Get price range
    price_range = medicine.get_price_range()
    
    # Get total availability
    total_available = PharmacyInventory.objects.filter(
        batch__medicine=medicine,
        current_stock__gt=0
    ).aggregate(total=Sum('current_stock'))['total'] or 0
    
    # Get pharmacy count
    pharmacy_count = PharmacyInventory.objects.filter(
        batch__medicine=medicine,
        current_stock__gt=0
    ).values('pharmacist').distinct().count()
    
    # Get all batches with details
    batches = medicine.batches.filter(is_active=True).select_related('medicine__manufacturer')
    
    # Get recent batch with most stock
    recent_batches = medicine.batches.filter(
        is_active=True,
        quantity__gt=0
    ).order_by('-manufacturing_date')[:5]
    
    return render(request, 'frontend/patient/medicine_detail.html', {
        'medicine': medicine,
        'min_price': price_range.get('min_price'),
        'max_price': price_range.get('max_price'),
        'total_available': total_available,
        'pharmacy_count': pharmacy_count,
        'batches': batches,
        'recent_batches': recent_batches,
    })


@login_required
def medicine_trace(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    # All batches for the medicine, with manufacturer and whether any pharmacy has stock
    from django.db.models import Sum
    batches = (MedicineBatch.objects
               .filter(medicine=medicine)
               .select_related('medicine')
               .order_by('-manufacturing_date'))
    stock_by_batch = (PharmacyInventory.objects
                      .filter(batch__medicine=medicine)
                      .values('batch')
                      .annotate(total_stock=Sum('current_stock')))
    totals = {row['batch']: row['total_stock'] for row in stock_by_batch}
    batch_rows = []
    for b in batches:
        batch_rows.append({
            'batch': b,
            'total_stock': totals.get(b.id, 0) or 0,
        })
    return render(request, 'frontend/patient/medicine_trace.html', {
        'medicine': medicine,
        'batch_rows': batch_rows,
    })


@login_required
def medicine_manufacturers(request, medicine_id):
    """Return JSON list of manufacturers for a given medicine id."""
    from django.http import JsonResponse
    try:
        med = Medicine.objects.get(id=medicine_id)
    except Medicine.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Medicine not found'}, status=404)
    # Find manufacturers who have available inventory for this medicine
    from django.db.models import F
    inv_qs = Inventory.objects.filter(batch__medicine=med).annotate(available=F('current_stock') - F('reserved_stock')).filter(available__gt=0)
    man_ids = inv_qs.values_list('batch__medicine__manufacturer', flat=True).distinct()
    mans = User.objects.filter(id__in=man_ids)
    data = [{'id': m.id, 'name': m.get_full_name() or m.username} for m in mans]
    return JsonResponse({'ok': True, 'manufacturers': data})


# Pharmacist location settings
@login_required
def pharmacist_location_settings(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    profile, _ = PharmacistProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.pharmacy_name = request.POST.get('pharmacy_name', '')
        profile.address = request.POST.get('address', '')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        profile.latitude = lat or None
        profile.longitude = lng or None
        profile.phone = request.POST.get('phone', '')
        profile.save()
        messages.success(request, 'Location updated')
        return redirect('frontend:pharmacist_location_settings')
    return render(request, 'frontend/pharmacist/location_settings.html', {'profile': profile})


@login_required
def pharmacist_transfers(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    incoming_transfers = MedicineTransfer.objects.filter(
        to_user=request.user, is_completed=False
    ).select_related('from_user', 'batch__medicine').order_by('-transfer_date')[:50]
    return render(request, 'frontend/pharmacist/pharmacist_transfers.html', {'incoming_transfers': incoming_transfers})


@login_required
def accept_transfer(request, transfer_id):
    """Pharmacist accepts an incoming transfer: add stock to their PharmacyInventory and mark transfer completed."""
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')

    try:
        transfer = MedicineTransfer.objects.get(id=transfer_id, to_user=request.user)
    except MedicineTransfer.DoesNotExist:
        messages.error(request, 'Transfer not found')
        return redirect('frontend:pharmacist_transfers')

    if transfer.is_completed:
        messages.info(request, 'Transfer already completed')
        return redirect('frontend:pharmacist_transfers')

    # Ensure a PharmacyInventory row exists for the pharmacist (the post_save signal on MedicineTransfer
    # will create it when the transfer is created). Do not manually increment stock here because the
    # pre_save signal handler `apply_completed_transfer_to_inventory` will add the quantity when the
    # transfer is marked completed. Avoid double-applying the quantity.
    PharmacyInventory.objects.get_or_create(
        pharmacist=request.user,
        batch=transfer.batch,
        defaults={'current_stock': 0}
    )

    transfer.is_completed = True
    transfer.save()

    # Mark any linked ReservationRequest(s) as transferred if they reference this transfer id in their note
    try:
        from inventory.models import ReservationRequest
        linked = ReservationRequest.objects.filter(note__icontains=f"transfer_id:{transfer.id}")
        for req in linked:
            req.status = ReservationRequest.STATUS_TRANSFERRED
            req.save()
    except Exception:
        pass

    messages.success(request, 'Transfer accepted and stock added to your inventory')
    return redirect('frontend:pharmacist_transfers')


@login_required
def pharmacist_inventory(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    
    # Get filter parameters
    search_query = request.GET.get('q', '').strip()
    stock_filter = request.GET.get('stock', 'all')  # all, low, out
    expiry_filter = request.GET.get('expiry', 'all')  # all, fresh, expiring, expired
    sort_by = request.GET.get('sort', 'name')  # name, stock, expiry, value
    
    # Base queryset
    items = PharmacyInventory.objects.filter(
        pharmacist=request.user
    ).select_related('batch__medicine', 'batch__medicine__manufacturer')
    
    # Search filter
    if search_query:
        items = items.filter(
            Q(batch__medicine__name__icontains=search_query) |
            Q(batch__medicine__generic_name__icontains=search_query) |
            Q(batch__batch_number__icontains=search_query)
        )
    
    # Stock level filter
    if stock_filter == 'low':
        items = items.filter(current_stock__lte=10, current_stock__gt=0)
    elif stock_filter == 'out':
        items = items.filter(current_stock=0)
    
    # Expiry filter
    today = date.today()
    if expiry_filter == 'fresh':
        items = items.filter(batch__expiry_date__gt=today + timedelta(days=30))
    elif expiry_filter == 'expiring':
        items = items.filter(
            batch__expiry_date__lte=today + timedelta(days=30),
            batch__expiry_date__gt=today
        )
    elif expiry_filter == 'expired':
        items = items.filter(batch__expiry_date__lte=today)
    
    # Sorting
    if sort_by == 'stock':
        items = items.order_by('current_stock')
    elif sort_by == 'expiry':
        items = items.order_by('batch__expiry_date')
    elif sort_by == 'value':
        items = items.order_by('-current_stock')  # Simplified
    else:
        items = items.order_by('batch__medicine__name')
    
    # Calculate statistics
    all_items = PharmacyInventory.objects.filter(pharmacist=request.user)
    total_items = all_items.count()
    total_value = sum([
        float(item.get_price() or 0) * item.current_stock 
        for item in all_items.select_related('batch')
    ])
    low_stock_count = all_items.filter(
        current_stock__lte=10,
        current_stock__gt=0
    ).count()
    expiring_count = all_items.filter(
        batch__expiry_date__lte=today + timedelta(days=30),
        batch__expiry_date__gt=today
    ).count()
    
    context = {
        'items': items,
        'search_query': search_query,
        'stock_filter': stock_filter,
        'expiry_filter': expiry_filter,
        'sort_by': sort_by,
        'total_items': total_items,
        'total_value': round(total_value, 2),
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
    }
    
    return render(request, 'frontend/pharmacist/inventory.html', context)

@login_required
@user_passes_test(is_manufacturer)
def manufacturer_dashboard(request):
    user = request.user
    
    # Get statistics
    total_medicines = Medicine.objects.filter(manufacturer=user, is_active=True).count()
    total_batches = MedicineBatch.objects.filter(medicine__manufacturer=user, is_active=True).count()
    total_inventory = Inventory.objects.filter(batch__medicine__manufacturer=user).aggregate(
        total_stock=Sum('current_stock')
    )['total_stock'] or 0
    
    # Get expiring batches (within 30 days)
    warning_date = date.today() + timedelta(days=30)
    expiring_batches = MedicineBatch.objects.filter(
        medicine__manufacturer=user,
        expiry_date__lte=warning_date,
        is_active=True
    ).select_related('medicine', 'inventory')
    
    # Get low stock medicines
    low_stock_inventory = Inventory.objects.filter(
        batch__medicine__manufacturer=user,
        current_stock__lte=F('minimum_stock_level')
    ).select_related('batch__medicine')
    
    # Recent transfers
    recent_transfers = MedicineTransfer.objects.filter(
        from_user=user
    ).select_related('to_user', 'batch__medicine').order_by('-transfer_date')[:5]
    
    context = {
        'total_medicines': total_medicines,
        'total_batches': total_batches,
        'total_inventory': total_inventory,
        'expiring_batches': expiring_batches,
        'low_stock_inventory': low_stock_inventory,
        'recent_transfers': recent_transfers,
    }
    
    return render(request, 'frontend/manufacturer/manufacturer_dashboard.html', context)

@login_required
@user_passes_test(is_manufacturer)
def medicine_list(request):
    user = request.user
    medicines = Medicine.objects.filter(manufacturer=user).order_by('name')
    
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.manufacturer = user
            medicine.save()
            messages.success(request, f'Medicine "{medicine.name}" created successfully!')
            return redirect('frontend:medicine_list')
    else:
        form = MedicineForm()
    
    context = {
        'medicines': medicines,
        'form': form,
    }
    return render(request, 'frontend/manufacturer/medicine_list.html', context)


@user_passes_test(is_manufacturer)
def edit_medicine(request, medicine_id):
    user = request.user
    medicine = get_object_or_404(Medicine, id=medicine_id, manufacturer=user)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine updated successfully')
            return redirect('frontend:medicine_list')
    else:
        form = MedicineForm(instance=medicine)

    return render(request, 'frontend/manufacturer/medicine_edit.html', {
        'form': form,
        'medicine': medicine,
    })


@user_passes_test(is_manufacturer)
def medicine_detail_simple(request, medicine_id):
    """A simplified, robust detail view that avoids rendering any risky fields directly."""
    medicine = get_object_or_404(Medicine, id=medicine_id, manufacturer=request.user)
    # Only pass a safe subset of fields to the template
    safe_context = {
        'id': medicine.id,
        'name': str(medicine.name) if medicine.name is not None else '',
        'generic_name': str(medicine.generic_name) if medicine.generic_name is not None else '',
        'strength': str(medicine.strength) if medicine.strength is not None else '',
        'dosage_form': str(medicine.dosage_form) if medicine.dosage_form is not None else '',
        'is_active': medicine.is_active,
        'created_at': medicine.created_at,
    }
    return render(request, 'frontend/manufacturer/medicine_detail_simple.html', safe_context)

@login_required
@user_passes_test(is_manufacturer)
def medicine_detail(request, medicine_id):
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id, manufacturer=request.user)
        batches = MedicineBatch.objects.filter(medicine=medicine, is_active=True).order_by('-manufacturing_date')

        # Defensive sanitization: some DB values may contain raw bytes that cannot be
        # decoded as UTF-8 which raises UnicodeDecodeError when templates render them.
        # Coerce CharField/TextField values to safe strings for rendering only.
        def _sanitize_instance_text_fields(instance):
            for field in getattr(instance._meta, 'fields', []):
                try:
                    ftype = field.get_internal_type()
                except Exception:
                    continue
                if ftype in ('CharField', 'TextField'):
                    name = field.name
                    try:
                        val = getattr(instance, name, None)
                    except Exception:
                        # If accessing the attribute raises (e.g., decoding in driver), skip
                        continue
                    if isinstance(val, (bytes, bytearray)):
                        try:
                            safe = val.decode('utf-8')
                        except UnicodeDecodeError:
                            safe = val.decode('utf-8', 'replace')
                        setattr(instance, name, safe)
                    elif val is not None and not isinstance(val, str):
                        # Ensure non-str values (rare) are converted safely
                        try:
                            setattr(instance, name, str(val))
                        except Exception:
                            setattr(instance, name, '')

        _sanitize_instance_text_fields(medicine)
        for b in batches:
            _sanitize_instance_text_fields(b)

        context = {
            'medicine': medicine,
            'batches': batches,
        }
        return render(request, 'frontend/manufacturer/medicine_detail.html', context)
    except UnicodeDecodeError:
        # Fallback: render a minimal safe page to avoid 500. Try to fetch simple name via values()
        simple = Medicine.objects.filter(id=medicine_id).values('id', 'name').first()
        med_name = simple.get('name') if simple else f'Medicine {medicine_id}'
        # Ensure med_name is safe str
        if isinstance(med_name, (bytes, bytearray)):
            try:
                med_name = med_name.decode('utf-8')
            except UnicodeDecodeError:
                med_name = med_name.decode('utf-8', 'replace')
        return render(request, 'frontend/manufacturer/medicine_detail_error.html', {
            'medicine_name': med_name,
            'medicine_id': medicine_id,
        })

@login_required
@user_passes_test(is_manufacturer)
def batch_list(request):
    user = request.user
    batches = MedicineBatch.objects.filter(medicine__manufacturer=user, is_active=True).select_related('medicine').order_by('-manufacturing_date')
    
    if request.method == 'POST':
        form = MedicineBatchForm(request.POST, manufacturer_user=user)
        if form.is_valid():
            batch = form.save()
            
            # Create inventory for the batch
            Inventory.objects.create(
                batch=batch,
                current_stock=batch.quantity,
                minimum_stock_level=10
            )
            
            messages.success(request, f'Batch {batch.batch_number} created successfully!')
            return redirect('frontend:batch_list')
    else:
        form = MedicineBatchForm(manufacturer_user=user)
    
    context = {
        'batches': batches,
        'form': form,
    }
    return render(request, 'frontend/manufacturer/batch_list.html', context)

@login_required
@user_passes_test(is_manufacturer)
def inventory_management(request):
    user = request.user
    inventory_items = Inventory.objects.filter(
        batch__medicine__manufacturer=user
    ).select_related('batch__medicine').order_by('batch__medicine__name')
    
    if request.method == 'POST':
        inventory_id = request.POST.get('inventory_id')
        new_stock = request.POST.get('new_stock')
        new_min_level = request.POST.get('new_min_level')
        
        if inventory_id and new_stock and new_min_level:
            try:
                inventory = Inventory.objects.get(id=inventory_id, batch__medicine__manufacturer=user)
                inventory.current_stock = int(new_stock)
                inventory.minimum_stock_level = int(new_min_level)
                inventory.save()
                messages.success(request, 'Inventory updated successfully!')
            except (Inventory.DoesNotExist, ValueError):
                messages.error(request, 'Invalid data provided!')
    
    # Attach pending requests directly to each inventory item for template ease
    for it in inventory_items:
        pending = list(ReservationRequest.objects.filter(manufacturer=user, medicine=it.batch.medicine, status=ReservationRequest.STATUS_PENDING).select_related('pharmacy'))
        setattr(it, 'pending_requests', pending)

    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'frontend/manufacturer/inventory_management.html', context)


@login_required
@user_passes_test(is_manufacturer)
def manufacturer_accept_reservation(request, inventory_id):
    """UI-only endpoint: manufacturer accepts a request.
    Currently this does not alter inventory unless explicit backend logic is desired.
    It will show a success message and redirect back to inventory page.
    """
    user = request.user
    if request.method != 'POST':
        return redirect('frontend:inventory_management')

    quantity = request.POST.get('quantity') or 0
    # Keep it UI-only: validate inputs and show a message
    try:
        qty = int(quantity)
        if qty <= 0:
            raise ValueError()
    except Exception:
        messages.error(request, 'Invalid quantity provided')
        return redirect('frontend:inventory_management')

    # Confirm inventory exists (read-only)
    try:
        inv = Inventory.objects.get(id=inventory_id, batch__medicine__manufacturer=user)
        med_name = inv.batch.medicine.name
    except Inventory.DoesNotExist:
        messages.error(request, 'Inventory item not found')
        return redirect('frontend:inventory_management')

    # UI action: mark accepted (no DB change) — message only
    messages.success(request, f'Accepted reservation of {qty} units for {med_name} (inventory id {inventory_id}).')
    return redirect('frontend:inventory_management')


@login_required
def request_reservation(request, inventory_id):
    """Pharmacist UI: request a reservation from a manufacturer for a specific inventory item.
    This is UI-first: we capture desired quantity and display a confirmation message.
    If you want persistence (creating a MedicineTransfer or similar), I can add that.
    """
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_inventory')
    if request.method != 'POST':
        return redirect('frontend:pharmacist_inventory')

    quantity = request.POST.get('quantity') or 0
    try:
        qty = int(quantity)
        if qty <= 0:
            raise ValueError()
    except Exception:
        messages.error(request, 'Please provide a valid quantity')
        return redirect('frontend:pharmacist_inventory')

    # Verify inventory exists
    try:
        inv = PharmacyInventory.objects.get(id=inventory_id)
        med_name = inv.batch.medicine.name
    except PharmacyInventory.DoesNotExist:
        messages.error(request, 'Selected inventory item not found')
        return redirect('frontend:pharmacist_inventory')
    # Check total available across all manufacturers for this medicine
    from django.db.models import F, Sum
    total_available = (Inventory.objects
                       .filter(batch__medicine=inv.batch.medicine)
                       .aggregate(total=Sum(F('current_stock') - F('reserved_stock')))['total']) or 0

    if total_available < qty:
        messages.error(request, f'Insufficient available stock across manufacturers (available: {total_available}).')
        return redirect('frontend:pharmacist_inventory')

    # UI-only: create a generic request or notify — for now show success and redirect
    messages.success(request, f'Request for {qty} units of {med_name} sent to manufacturers (UI-only).')
    return redirect('frontend:pharmacist_inventory')


@login_required
def create_reservation_request(request):
    """Handle pharmacist submissions selecting a manufacturer for a medicine.
    Expects POST with manufacturer_id, medicine_id, quantity (validated by ReservationRequestForm)
    """
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_inventory')

    if request.method != 'POST':
        return redirect('frontend:pharmacist_inventory')

    form = ReservationRequestForm(request.POST)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, err)
        return redirect('frontend:pharmacist_inventory')

    manufacturer_id = form.cleaned_data['manufacturer_id']
    medicine_id = form.cleaned_data['medicine_id']
    quantity = form.cleaned_data['quantity']
    note = form.cleaned_data.get('note')

    from inventory.models import ReservationRequest
    from authentication_app.models import User
    from medicine.models import Medicine

    try:
        manufacturer = User.objects.get(id=manufacturer_id, role=User.ROLE_MANUFACTURER)
        medicine = Medicine.objects.get(id=medicine_id)
    except Exception:
        messages.error(request, 'Invalid manufacturer or medicine selected')
        return redirect('frontend:pharmacist_inventory')

    # Allow pharmacists to send requests to manufacturers even if the manufacturer does not currently have available stock.
    # Create a ReservationRequest record
    req = ReservationRequest.objects.create(
        pharmacy=request.user,
        manufacturer=manufacturer,
        medicine=medicine,
        quantity=quantity,
        note=note or ''
    )

    success_message = f'Request sent to {manufacturer.get_full_name() or manufacturer.username} for {quantity} units of {medicine.name}.'
    # Detect AJAX requests via the X-Requested-With header set by the frontend fetch calls
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax:
        from django.http import JsonResponse
        return JsonResponse({'ok': True, 'message': success_message})

    messages.success(request, success_message)
    return redirect('frontend:pharmacist_inventory')


@login_required
def pharmacist_reservations(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_inventory')
    from inventory.models import ReservationRequest
    reqs = ReservationRequest.objects.filter(pharmacy=request.user).order_by('-created_at')
    return render(request, 'frontend/pharmacist/reservations.html', {'requests': reqs})


@login_required
@user_passes_test(is_manufacturer)
def manufacturer_reservation_list(request):
    """List requests sent to this manufacturer."""
    from inventory.models import ReservationRequest
    requests_qs = ReservationRequest.objects.filter(manufacturer=request.user).order_by('-created_at')
    return render(request, 'frontend/manufacturer/reservation_list.html', {'requests': requests_qs})


@login_required
@user_passes_test(is_manufacturer)
def manufacturer_inventory_detail(request, inventory_id):
    """Show details for a single Inventory item (manufacturer view)."""
    inv = get_object_or_404(Inventory, id=inventory_id, batch__medicine__manufacturer=request.user)
    # Get related requests for this medicine targeted at this manufacturer
    from inventory.models import ReservationRequest
    reservations = ReservationRequest.objects.filter(manufacturer=request.user, medicine=inv.batch.medicine).order_by('-created_at')

    context = {
        'inventory': inv,
        'reservations': reservations,
    }
    return render(request, 'frontend/manufacturer/inventory_detail.html', context)


@login_required
@user_passes_test(is_manufacturer)
def respond_reservation_request(request, request_id, action):
    """Manufacturer accepts or rejects a reservation request. If accepted, optionally create a MedicineTransfer.
    action: 'accept' or 'reject'
    """
    from inventory.models import ReservationRequest
    from inventory.models import MedicineTransfer
    from django.utils import timezone

    req = get_object_or_404(ReservationRequest, id=request_id, manufacturer=request.user)

    if req.status != ReservationRequest.STATUS_PENDING:
        messages.info(request, 'This request has already been processed.')
        return redirect('frontend:manufacturer_reservations')

    if action == 'accept':
        # Allocate and create transfers under a DB transaction
        with transaction.atomic():
            req.status = ReservationRequest.STATUS_RESERVED
            req.responded_by = request.user
            req.responded_at = timezone.now()
            req.save()

            remaining = req.quantity or 0
            allocated = []
            invs = (Inventory.objects
                    .select_for_update()
                    .filter(
                        batch__medicine=req.medicine,
                        batch__medicine__manufacturer=request.user
                    )
                    .select_related('batch')
                    .order_by('batch__manufacturing_date'))

            for inv in invs:
                avail = (inv.current_stock or 0) - (inv.reserved_stock or 0)
                if avail <= 0:
                    continue
                take = min(avail, remaining)
                if take <= 0:
                    continue
                Inventory.objects.filter(pk=inv.pk).update(
                    reserved_stock=F('reserved_stock') + take
                )
                allocated.append((inv, take))
                remaining -= take
                if remaining <= 0:
                    break

            if remaining > 0:
                messages.warning(request, f'Request accepted but only partially allocated ({(req.quantity or 0) - remaining}/{req.quantity}).')
            else:
                messages.success(request, f'Request accepted and {req.quantity} units reserved for {req.pharmacy.username}.')

            created_transfer_ids = []
            for inv_obj, qty_taken in allocated:
                if qty_taken <= 0:
                    continue
                transfer = MedicineTransfer.objects.create(
                    transfer_type='manufacturer_to_pharmacy',
                    from_user=request.user,
                    to_user=req.pharmacy,
                    batch=inv_obj.batch,
                    quantity=qty_taken,
                    notes=f'Auto-created transfer for request {req.id}',
                    is_completed=False,
                )
                Inventory.objects.filter(pk=inv_obj.pk).update(
                    current_stock=F('current_stock') - qty_taken,
                    reserved_stock=F('reserved_stock') - qty_taken,
                )
                created_transfer_ids.append(str(transfer.id))

            if created_transfer_ids:
                extra = req.note or ''
                extra += '|transfer_id:' + ','.join(created_transfer_ids)
                req.note = extra
                req.save()

        from django.urls import reverse
        return redirect(reverse('frontend:inventory_management'))

    else:
        # reject
        req.status = ReservationRequest.STATUS_REJECTED
        req.responded_by = request.user
        req.responded_at = timezone.now()
        req.save()
    messages.success(request, 'Request rejected')

    return redirect('frontend:manufacturer_reservations')


@login_required
@user_passes_test(is_manufacturer)
def reservation_detail(request, reservation_id):
    from inventory.models import ReservationRequest
    req = get_object_or_404(ReservationRequest, id=reservation_id, manufacturer=request.user)
    # Find allocations (Inventory entries where reserved_stock increased) — best-effort: show seller inventory and reserved amounts
    invs = Inventory.objects.filter(batch__medicine=req.medicine, batch__medicine__manufacturer=request.user).select_related('batch')
    return render(request, 'frontend/manufacturer/reservation_detail.html', {'request_obj': req, 'inventories': invs})

@login_required
@user_passes_test(is_manufacturer)
def transfer_medicine(request):
    user = request.user
    
    if request.method == 'POST':
        form = MedicineTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.from_user = user

            # Atomic stock decrement to avoid race conditions
            with transaction.atomic():
                batch = transfer.batch
                inv = Inventory.objects.select_for_update().get(pk=batch.inventory.pk)
                if (inv.current_stock or 0) < (transfer.quantity or 0):
                    messages.error(request, 'Insufficient stock to transfer the requested quantity.')
                    return redirect('frontend:transfer_medicine')
                Inventory.objects.filter(pk=inv.pk).update(
                    current_stock=F('current_stock') - (transfer.quantity or 0)
                )
                transfer.save()

            # If this transfer was created as part of a reservation flow, link it by noting the reservation id
            reservation_id = request.POST.get('reservation_id')
            if reservation_id:
                from inventory.models import ReservationRequest
                try:
                    req = ReservationRequest.objects.get(id=int(reservation_id), pharmacy__isnull=False)
                    # Mark as accepted/transferred in note (avoid schema changes)
                    req.status = ReservationRequest.STATUS_RESERVED
                    extra = req.note or ''
                    extra += f"|transfer_id:{transfer.id}"
                    req.note = extra
                    req.save()
                except Exception:
                    # ignore silently; this is best-effort tagging
                    pass

            messages.success(request, f'Transfer of {transfer.quantity} units created successfully!')
            return redirect('frontend:transfer_medicine')
    else:
        form = MedicineTransferForm()
    
    # Set up form fields after creation
    if hasattr(form, 'fields'):
        # Filter batches to only show those from the manufacturer
        form.fields['batch'].queryset = MedicineBatch.objects.filter(
            medicine__manufacturer=user,
            is_active=True
        ).select_related('medicine', 'inventory')
        
        # Filter recipients to only show pharmacists and doctors
        form.fields['to_user'].queryset = User.objects.filter(
            role__in=[User.ROLE_PHARMACIST, User.ROLE_DOCTOR]
        )
        
        # Set from_user to manufacturer
        form.fields['from_user'].initial = user
        form.fields['from_user'].widget = forms.HiddenInput()
    
    # Get available batches and potential recipients
    available_batches = MedicineBatch.objects.filter(
        medicine__manufacturer=user,
        is_active=True
    ).select_related('medicine', 'inventory').filter(inventory__current_stock__gt=0)
    
    # Get recent transfers
    recent_transfers = MedicineTransfer.objects.filter(
        from_user=user
    ).select_related('to_user', 'batch__medicine').order_by('-transfer_date')[:10]
    
    # Prefill from query params (when redirected after accepting a reservation)
    prefill = {
        'batch_id': request.GET.get('batch_id'),
        'quantity': request.GET.get('quantity'),
        'reservation_id': request.GET.get('reservation_id'),
    }

    context = {
        'form': form,
        'available_batches': available_batches,
        'recent_transfers': recent_transfers,
        'prefill': prefill,
    }
    return render(request, 'frontend/manufacturer/transfer_medicine.html', context)
