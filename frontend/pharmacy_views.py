from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Avg, Max, Min
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.http import HttpResponse, JsonResponse
import csv

from authentication_app.models import User
from medicine.models import Medicine, MedicineBatch
from inventory.models import (
    PharmacyInventory, MedicineTransfer, ReservationRequest,
    Sale, SaleItem, ReorderAlert
)
from prescription.models import Prescription, Notification
from inventory.forms import DispensePrescriptionForm, SaleForm, ReorderAlertForm


@login_required
def enhanced_pharmacist_dashboard(request):
    """Enhanced pharmacist dashboard with real-time widgets and analytics"""
    user = request.user
    if not user.is_pharmacist:
        return redirect('frontend:home')
    
    # Get today and date ranges
    today = date.today()
    thirty_days = today + timedelta(days=30)
    seven_days = today + timedelta(days=7)
    
    # === LOW STOCK ALERTS ===
    low_stock_threshold = 10
    low_stock_items = PharmacyInventory.objects.filter(
        pharmacist=user,
        current_stock__lt=low_stock_threshold,
        current_stock__gt=0
    ).select_related('batch__medicine', 'batch__medicine__manufacturer').order_by('current_stock')[:10]
    
    low_stock_count = PharmacyInventory.objects.filter(
        pharmacist=user,
        current_stock__lt=low_stock_threshold,
        current_stock__gt=0
    ).count()
    
    # === EXPIRY WARNINGS ===
    expiring_soon = PharmacyInventory.objects.filter(
        pharmacist=user,
        batch__expiry_date__lte=thirty_days,
        batch__expiry_date__gt=today,
        current_stock__gt=0
    ).select_related('batch__medicine').order_by('batch__expiry_date')[:10]
    
    expiring_count = expiring_soon.count()
    
    # Critical expiring (7 days)
    critical_expiring = PharmacyInventory.objects.filter(
        pharmacist=user,
        batch__expiry_date__lte=seven_days,
        batch__expiry_date__gt=today,
        current_stock__gt=0
    ).count()
    
    # Expired items
    expired_items = PharmacyInventory.objects.filter(
        pharmacist=user,
        batch__expiry_date__lte=today,
        current_stock__gt=0
    ).count()
    
    # === PENDING PRESCRIPTIONS ===
    pending_prescriptions = Prescription.objects.filter(
        status='pending'
    ).select_related('patient', 'doctor', 'medicine').order_by('-prescribed_date')[:10]
    
    pending_prescriptions_count = Prescription.objects.filter(status='pending').count()
    
    # Urgent prescriptions (older than 2 days)
    urgent_date = timezone.now() - timedelta(days=2)
    urgent_prescriptions_count = Prescription.objects.filter(
        status='pending',
        prescribed_date__lt=urgent_date
    ).count()
    
    # === TODAY'S SALES SUMMARY ===
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = Sale.objects.filter(
        pharmacist=user,
        sale_date__gte=today_start
    )
    
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or 0
    today_transactions = today_sales.count()
    
    # Calculate today's profit
    today_profit = 0
    for sale in today_sales.prefetch_related('items__batch'):
        today_profit += sale.profit
    
    # === INVENTORY SUMMARY ===
    total_inventory_items = PharmacyInventory.objects.filter(
        pharmacist=user,
        current_stock__gt=0
    ).count()
    
    total_stock_units = PharmacyInventory.objects.filter(
        pharmacist=user
    ).aggregate(total=Sum('current_stock'))['total'] or 0
    
    # Calculate inventory value
    inventory_value = 0
    for inv in PharmacyInventory.objects.filter(pharmacist=user).select_related('batch'):
        price = inv.get_price() or 0
        inventory_value += float(price) * inv.current_stock
    
    # === REORDER ALERTS ===
    pending_reorder_alerts = ReorderAlert.objects.filter(
        pharmacist=user,
        status=ReorderAlert.STATUS_PENDING
    ).select_related('pharmacy_inventory__batch__medicine').order_by('-created_at')[:5]
    
    pending_reorder_count = pending_reorder_alerts.count()
    
    # === RECENT ACTIVITY ===
    recent_sales = Sale.objects.filter(
        pharmacist=user
    ).order_by('-sale_date')[:5]
    
    incoming_transfers = MedicineTransfer.objects.filter(
        to_user=user,
        is_completed=False
    ).select_related('from_user', 'batch__medicine').order_by('-transfer_date')[:5]
    
    # === WEEK COMPARISON ===
    week_ago = today - timedelta(days=7)
    week_ago_start = timezone.now() - timedelta(days=7)
    
    last_week_revenue = Sale.objects.filter(
        pharmacist=user,
        sale_date__gte=week_ago_start,
        sale_date__lt=today_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate revenue change percentage
    if last_week_revenue > 0:
        revenue_change = ((float(today_revenue) - float(last_week_revenue)) / float(last_week_revenue)) * 100
    else:
        revenue_change = 100 if today_revenue > 0 else 0

    # Absolute value for templates (Django template has no built-in abs filter)
    revenue_change_abs = abs(revenue_change)
    
    context = {
        # Alerts and warnings
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'expiring_soon': expiring_soon,
        'expiring_count': expiring_count,
        'critical_expiring': critical_expiring,
        'expired_items': expired_items,
        
        # Prescriptions
        'pending_prescriptions': pending_prescriptions,
        'pending_prescriptions_count': pending_prescriptions_count,
        'urgent_prescriptions_count': urgent_prescriptions_count,
        
        # Sales summary
        'today_revenue': round(float(today_revenue), 2),
        'today_transactions': today_transactions,
        'today_profit': round(today_profit, 2),
        'revenue_change': round(revenue_change, 1),
        'revenue_change_abs': round(revenue_change_abs, 1),
        
        # Inventory
        'total_inventory_items': total_inventory_items,
        'total_stock_units': total_stock_units,
        'inventory_value': round(inventory_value, 2),
        
        # Reorder
        'pending_reorder_alerts': pending_reorder_alerts,
        'pending_reorder_count': pending_reorder_count,
        
        # Recent activity
        'recent_sales': recent_sales,
        'incoming_transfers': incoming_transfers,
    }
    
    return render(request, 'frontend/pharmacist/pharmacist_dashboard.html', context)


@login_required
def prescription_queue(request):
    """Prescription search - pharmacist must search by patient ID or username"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    search_query = request.GET.get('q', '').strip()
    prescriptions = []
    patient_found = False
    
    # Only show prescriptions if search query provided
    if search_query:
        prescriptions = Prescription.objects.filter(
            Q(patient__username__iexact=search_query) |
            Q(patient__id=search_query if search_query.isdigit() else None) |
            Q(patient__full_name__icontains=search_query)
        ).select_related(
            'patient', 'doctor', 'medicine', 'dispensed_by'
        ).order_by('-prescribed_date')
        
        patient_found = prescriptions.exists()
    
    context = {
        'prescriptions': prescriptions,
        'search_query': search_query,
        'patient_found': patient_found,
    }
    
    return render(request, 'frontend/pharmacist/prescription_queue.html', context)


@login_required
def dispense_prescription(request, prescription_id):
    """Dispense a prescription and record sale"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    if prescription.status != 'pending':
        messages.error(request, 'This prescription has already been processed.')
        return redirect('frontend:prescription_queue')
    
    # Get available batches for this medicine in pharmacy inventory
    available_batches = PharmacyInventory.objects.filter(
        pharmacist=request.user,
        batch__medicine=prescription.medicine,
        current_stock__gt=0
    ).select_related('batch')
    
    if request.method == 'POST':
        form = DispensePrescriptionForm(request.POST, pharmacist=request.user)
        
        if form.is_valid():
            batch_id = form.cleaned_data['batch_id']
            quantity = form.cleaned_data['quantity']
            payment_method = form.cleaned_data['payment_method']
            notes = form.cleaned_data.get('notes', '')
            
            # Get inventory
            inventory = PharmacyInventory.objects.get(
                pharmacist=request.user,
                batch_id=batch_id
            )
            
            # Create sale
            unit_price = inventory.get_price()
            total_amount = unit_price * quantity
            
            sale = Sale.objects.create(
                pharmacist=request.user,
                patient=prescription.patient,
                prescription=prescription,
                total_amount=total_amount,
                payment_method=payment_method,
                notes=notes
            )
            
            # Create sale item
            SaleItem.objects.create(
                sale=sale,
                batch=inventory.batch,
                pharmacy_inventory=inventory,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=total_amount
            )
            
            # Update inventory
            inventory.current_stock -= quantity
            inventory.save()
            
            # Update prescription
            prescription.status = 'dispensed'
            prescription.dispensed_by = request.user
            prescription.dispensed_date = timezone.now()
            prescription.dispensed_batch = inventory.batch
            prescription.save()
            
            # Create notification for patient
            Notification.objects.create(
                user=prescription.patient,
                notification_type='prescription_dispensed',
                title='Prescription Ready',
                message=f'Your prescription for {prescription.medicine.name} has been dispensed and is ready for pickup.'
            )
            
            messages.success(request, f'Prescription dispensed successfully. Sale #{sale.id} recorded.')
            return redirect('frontend:prescription_queue')
    else:
        form = DispensePrescriptionForm(
            initial={
                'prescription_id': prescription_id,
                'quantity': prescription.quantity
            },
            pharmacist=request.user
        )
    
    context = {
        'prescription': prescription,
        'available_batches': available_batches,
        'form': form,
    }
    
    return render(request, 'frontend/pharmacist/dispense_prescription.html', context)


@login_required
def sales_analytics(request):
    """Sales analytics dashboard with reports and charts"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    # Get date range parameters
    period = request.GET.get('period', 'week')  # day, week, month, custom
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = timezone.now()
    
    # Determine date range
    if period == 'day':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d'))
    else:
        start_date = today - timedelta(days=7)
        end_date = today
    
    # Get sales in period
    sales = Sale.objects.filter(
        pharmacist=request.user,
        sale_date__gte=start_date,
        sale_date__lte=end_date
    )
    
    # === SUMMARY STATISTICS ===
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_transactions = sales.count()
    average_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    
    # Calculate total profit
    total_profit = sum([sale.profit for sale in sales.prefetch_related('items__batch')])
    profit_margin = (total_profit / float(total_revenue) * 100) if total_revenue > 0 else 0
    
    # === TOP SELLING MEDICINES ===
    top_medicines = SaleItem.objects.filter(
        sale__pharmacist=request.user,
        sale__sale_date__gte=start_date,
        sale__sale_date__lte=end_date
    ).values(
        'batch__medicine__name',
        'batch__medicine__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        transaction_count=Count('sale', distinct=True)
    ).order_by('-total_revenue')[:10]
    
    # Calculate profit for each top medicine
    for item in top_medicines:
        medicine_items = SaleItem.objects.filter(
            sale__pharmacist=request.user,
            sale__sale_date__gte=start_date,
            sale__sale_date__lte=end_date,
            batch__medicine__id=item['batch__medicine__id']
        ).select_related('batch')
        
        medicine_profit = 0
        for sale_item in medicine_items:
            cost = float(sale_item.batch.cost_price or 0) * sale_item.quantity
            revenue = float(sale_item.unit_price) * sale_item.quantity
            medicine_profit += revenue - cost
        
        item['profit'] = round(medicine_profit, 2)
        item['profit_margin'] = round((medicine_profit / float(item['total_revenue']) * 100), 1) if item['total_revenue'] > 0 else 0
    
    # === DAILY BREAKDOWN ===
    if period == 'month':
        # Group by date
        daily_sales = sales.annotate(
            date=TruncDate('sale_date')
        ).values('date').annotate(
            revenue=Sum('total_amount'),
            transactions=Count('id')
        ).order_by('date')
    else:
        daily_sales = []
    
    # === PAYMENT METHOD BREAKDOWN ===
    payment_breakdown = sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')
    
    # === CUSTOMER STATISTICS ===
    unique_customers = sales.filter(patient__isnull=False).values('patient').distinct().count()
    prescription_sales = sales.filter(prescription__isnull=False).count()
    otc_sales = sales.filter(prescription__isnull=True).count()
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': round(float(total_revenue), 2),
        'total_transactions': total_transactions,
        'average_transaction': round(float(average_transaction), 2),
        'total_profit': round(total_profit, 2),
        'profit_margin': round(profit_margin, 1),
        'top_medicines': top_medicines,
        'daily_sales': daily_sales,
        'payment_breakdown': payment_breakdown,
        'unique_customers': unique_customers,
        'prescription_sales': prescription_sales,
        'otc_sales': otc_sales,
    }
    
    return render(request, 'frontend/pharmacist/sales_analytics.html', context)


@login_required
def export_sales_report(request):
    """Export sales report as CSV"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    # Get parameters
    period = request.GET.get('period', 'month')
    today = timezone.now()
    
    if period == 'day':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = today - timedelta(days=7)
    else:
        start_date = today - timedelta(days=30)
    
    # Get sales
    sales = Sale.objects.filter(
        pharmacist=request.user,
        sale_date__gte=start_date
    ).select_related('patient', 'prescription').prefetch_related('items__batch__medicine')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{period}_{today.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Sale ID', 'Date', 'Patient', 'Medicine', 'Quantity',
        'Unit Price', 'Subtotal', 'Payment Method', 'Prescription ID', 'Notes'
    ])
    
    for sale in sales:
        for item in sale.items.all():
            writer.writerow([
                sale.id,
                sale.sale_date.strftime('%Y-%m-%d %H:%M'),
                sale.patient.full_name if sale.patient else 'Walk-in',
                item.batch.medicine.name,
                item.quantity,
                item.unit_price,
                item.subtotal,
                sale.get_payment_method_display(),
                sale.prescription_id if sale.prescription else 'N/A',
                sale.notes or ''
            ])
    
    return response


@login_required
def reorder_management(request):
    """Manage reorder alerts and create reservation requests"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    # Get all reorder alerts
    alerts = ReorderAlert.objects.filter(
        pharmacist=request.user
    ).select_related(
        'pharmacy_inventory__batch__medicine',
        'pharmacy_inventory__batch__medicine__manufacturer',
        'reservation_request'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'pending')
    if status_filter and status_filter != 'all':
        alerts = alerts.filter(status=status_filter)
    
    context = {
        'alerts': alerts,
        'status_filter': status_filter,
    }
    
    return render(request, 'frontend/pharmacist/reorder_management.html', context)


@login_required
def create_reorder_request(request, alert_id):
    """Create a reservation request from a reorder alert"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    alert = get_object_or_404(ReorderAlert, id=alert_id, pharmacist=request.user)
    
    if alert.status != ReorderAlert.STATUS_PENDING:
        messages.error(request, 'This alert has already been processed.')
        return redirect('frontend:reorder_management')
    
    # Create reservation request
    medicine = alert.pharmacy_inventory.batch.medicine
    manufacturer = medicine.manufacturer
    
    reservation = ReservationRequest.objects.create(
        pharmacy=request.user,
        manufacturer=manufacturer,
        medicine=medicine,
        quantity=alert.suggested_quantity,
        note=f'Auto-reorder from low stock alert #{alert.id}'
    )
    
    # Update alert
    alert.status = ReorderAlert.STATUS_ORDERED
    alert.reservation_request = reservation
    alert.save()
    
    messages.success(request, f'Reservation request #{reservation.id} created successfully.')
    return redirect('frontend:pharmacist_reservations')


@login_required
def dismiss_reorder_alert(request, alert_id):
    """Dismiss a reorder alert"""
    if not request.user.is_pharmacist:
        return redirect('frontend:home')
    
    alert = get_object_or_404(ReorderAlert, id=alert_id, pharmacist=request.user)
    alert.status = ReorderAlert.STATUS_DISMISSED
    alert.save()
    
    messages.success(request, 'Reorder alert dismissed.')
    return redirect('frontend:reorder_management')
