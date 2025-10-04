from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, F
from django.db.models import Sum
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
    return render(request, 'frontend/patient/patient_dashboard.html')


@login_required
def doctor_dashboard(request):
    return render(request, 'frontend/doctor/doctor_dashboard.html')


@login_required
def pharmacist_dashboard(request):
    user = request.user
    # lightweight placeholder; full implementation appears later in file
    return render(request, 'frontend/pharmacist/pharmacist_dashboard.html')


@login_required
def pharmacist_medicine_search(request):
    if not request.user.is_pharmacist:
        return redirect('frontend:pharmacist_dashboard')

    q = (request.GET.get('q') or '').strip()
    medicines = Medicine.objects.filter(is_active=True)
    if q:
        medicines = medicines.filter(name__icontains=q) | medicines.filter(generic_name__icontains=q)

    # For each medicine compute total available across all manufacturers
    from django.db.models import Sum, F
    med_list = []
    for med in medicines.order_by('name'):
        total_available = (Inventory.objects.filter(batch__medicine=med).annotate(available=F('current_stock') - F('reserved_stock')).aggregate(total=Sum('available'))['total']) or 0
        med_list.append({'medicine': med, 'available': total_available})

    return render(request, 'frontend/pharmacist/medicine_search.html', {'med_rows': med_list, 'q': q})


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
    items = PharmacyInventory.objects.filter(pharmacist=request.user).select_related('batch__medicine')

    # Build rows list where each row contains the inventory item and available manufacturers for that medicine
    rows = []
    for item in items:
        med = item.batch.medicine
        # Only include manufacturers who have available stock for this medicine
        from django.db.models import F
        inv_qs = Inventory.objects.filter(batch__medicine=med).annotate(available=F('current_stock') - F('reserved_stock')).filter(available__gt=0)
        mans = User.objects.filter(id__in=inv_qs.values_list('batch__medicine__manufacturer', flat=True)).distinct()
        rows.append({'item': item, 'manufacturers': list(mans)})

    # Consolidated reservation list for the pharmacist (top-level)
    my_requests_all = list(ReservationRequest.objects.filter(pharmacy=request.user).order_by('-created_at')[:20])

    return render(request, 'frontend/pharmacist/inventory.html', {'rows': rows, 'my_requests_all': my_requests_all})

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
        # Mark reserved (accepted -> reserved)
        req.status = ReservationRequest.STATUS_RESERVED
        req.responded_by = request.user
        req.responded_at = timezone.now()
        req.save()

        # Reserve inventory: try to allocate req.quantity across manufacturer's Inventory batches
        remaining = req.quantity
        allocated = []
        try:
            invs = Inventory.objects.filter(
                batch__medicine=req.medicine,
                batch__medicine__manufacturer=request.user
            ).select_related('batch').order_by('batch__manufacturing_date')
            for inv in invs:
                avail = inv.available_stock
                if avail <= 0:
                    continue
                take = min(avail, remaining)
                inv.reserved_stock += take
                inv.save()
                allocated.append((inv, take))
                remaining -= take
                if remaining <= 0:
                    break

            # Set messages based on allocation result
            if remaining > 0:
                messages.warning(request, f'Request accepted but only partially allocated ({req.quantity - remaining}/{req.quantity}). Please transfer remaining units manually.')
            else:
                messages.success(request, f'Request accepted and {req.quantity} units reserved for {req.pharmacy.username}.')
        except Exception as e:
            messages.error(request, f'Accepted but reservation allocation failed: {e}')

        # After accepting, create MedicineTransfer records for each allocation so the transfer shows up
        # in the pharmacist's incoming transfers list. Decrement sender inventory current_stock accordingly.
        try:
            created_transfer_ids = []
            for inv_obj, qty_taken in allocated:
                if qty_taken <= 0:
                    continue
                # create transfer per allocated inventory batch
                transfer = MedicineTransfer.objects.create(
                    transfer_type='manufacturer_to_pharmacy',
                    from_user=request.user,
                    to_user=req.pharmacy,
                    batch=inv_obj.batch,
                    quantity=qty_taken,
                    notes=f'Auto-created transfer for request {req.id}',
                    is_completed=False,
                )
                # Decrement sender inventory current_stock by the transfer quantity
                try:
                    inv_obj.current_stock = max(0, (inv_obj.current_stock or 0) - qty_taken)
                    # Also reduce reserved_stock since we've allocated from reserved
                    inv_obj.reserved_stock = max(0, (inv_obj.reserved_stock or 0) - qty_taken)
                    inv_obj.save()
                except Exception:
                    # ignore inventory decrement errors but keep transfer record
                    pass

                created_transfer_ids.append(str(transfer.id))

            # Tag reservation note with created transfer ids
            if created_transfer_ids:
                extra = req.note or ''
                extra += '|transfer_id:' + ','.join(created_transfer_ids)
                req.note = extra
                req.save()

        except Exception as e:
            # if transfer creation failed, still proceed but warn
            messages.warning(request, f'Request accepted but automatic transfer creation failed: {e}')

        # After creating transfers, redirect to the manufacturer's transfers page
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
            
            # Update inventory
            batch = transfer.batch
            batch.inventory.current_stock -= transfer.quantity
            batch.inventory.save()
            
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
