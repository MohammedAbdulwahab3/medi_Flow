from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, F
from django import forms
from datetime import date, timedelta

from authentication_app.models import User
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, MedicineTransfer
from inventory.models import PharmacyInventory
from medicine.forms import MedicineForm, MedicineBatchForm
from inventory.forms import InventoryForm, MedicineTransferForm
from authentication_app.models import PharmacistProfile

def is_manufacturer(user):
    return user.is_authenticated and user.role == User.ROLE_MANUFACTURER

@login_required
def patient_dashboard(request):
    return render(request, 'frontend/patient/patient_dashboard.html')

@login_required
def doctor_dashboard(request):
    return render(request, 'frontend/doctor/doctor_dashboard.html')

@login_required
def pharmacist_dashboard(request):
    user = request.user
    
    # Get incoming transfers (transfers to this pharmacist)
    incoming_transfers = MedicineTransfer.objects.filter(
        to_user=user, is_completed=False
    ).select_related('from_user', 'batch__medicine').order_by('-transfer_date')[:10]
    
    # Get low stock items (if pharmacist has inventory)
    low_stock_items = Inventory.objects.filter(
        batch__medicine__manufacturer__isnull=False,  # Only show items from manufacturers
        current_stock__lte=F('minimum_stock_level')
    ).select_related('batch__medicine')[:5]
    
    context = {
        'incoming_transfers': incoming_transfers,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'frontend/pharmacist/pharmacist_dashboard.html', context)


@login_required
def pharmacist_transfers(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    transfers = MedicineTransfer.objects.filter(to_user=request.user).select_related('from_user', 'batch__medicine')
    return render(request, 'frontend/pharmacist/transfers.html', {'transfers': transfers})


@login_required
def accept_transfer(request, transfer_id):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    transfer = get_object_or_404(MedicineTransfer, id=transfer_id, to_user=request.user, is_completed=False)
    # add to PharmacyInventory or create
    from inventory.models import PharmacyInventory
    inv, _ = PharmacyInventory.objects.get_or_create(
        pharmacist=request.user,
        batch=transfer.batch,
        defaults={'current_stock': 0}
    )
    inv.current_stock += transfer.quantity
    inv.save()
    transfer.is_completed = True
    transfer.save()
    messages.success(request, 'Transfer accepted and stock added to your inventory')
    return redirect('frontend:pharmacist_transfers')


# Patient catalog views
@login_required
def medicine_catalog(request):
    q = (request.GET.get('q') or '').strip()
    medicines = Medicine.objects.filter(is_active=True)
    if q:
        medicines = medicines.filter(name__icontains=q) | medicines.filter(generic_name__icontains=q)
    medicines = medicines.order_by('name')
    return render(request, 'frontend/patient/catalog.html', {'medicines': medicines, 'q': q})


@login_required
def medicine_availability(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
    # Pharmacies with stock for any batch of this medicine
    inventories = PharmacyInventory.objects.filter(
        batch__medicine=medicine, current_stock__gt=0
    ).select_related('pharmacist__pharmacist_profile', 'batch')
    return render(request, 'frontend/patient/medicine_availability.html', {
        'medicine': medicine,
        'inventories': inventories,
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
def pharmacist_inventory(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')
    items = PharmacyInventory.objects.filter(pharmacist=request.user).select_related('batch__medicine')
    return render(request, 'frontend/pharmacist/inventory.html', {'items': items})

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

@login_required
@user_passes_test(is_manufacturer)
def medicine_detail(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id, manufacturer=request.user)
    batches = MedicineBatch.objects.filter(medicine=medicine, is_active=True).order_by('-manufacturing_date')
    
    context = {
        'medicine': medicine,
        'batches': batches,
    }
    return render(request, 'frontend/manufacturer/medicine_detail.html', context)

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
    
    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'frontend/manufacturer/inventory_management.html', context)

@login_required
@user_passes_test(is_manufacturer)
def transfer_medicine(request):
    user = request.user
    
    if request.method == 'POST':
        form = MedicineTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.from_user = user
            
            # Update inventory
            batch = transfer.batch
            batch.inventory.current_stock -= transfer.quantity
            batch.inventory.save()
            
            transfer.save()
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
    
    context = {
        'form': form,
        'available_batches': available_batches,
        'recent_transfers': recent_transfers,
    }
    return render(request, 'frontend/manufacturer/transfer_medicine.html', context)
