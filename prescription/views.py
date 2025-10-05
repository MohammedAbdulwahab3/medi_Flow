from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse

from authentication_app.models import User
from .models import (
    Prescription, PatientMedicalRecord, PatientHistoryEntry,
    DoctorProfile, PatientDoctorAssignment, Message, Notification
)
from inventory.models import PharmacyInventory
from .forms import (
    DoctorPrescriptionForm, PharmacistDispenseForm, DoctorHistoryEntryForm,
    DoctorProfileForm, MessageForm, MessageReplyForm, PatientDoctorAssignmentForm
)


def is_doctor(user):
    return user.is_authenticated and user.role == User.ROLE_DOCTOR


def is_pharmacist(user):
    return user.is_authenticated and user.role == User.ROLE_PHARMACIST


@login_required
@user_passes_test(is_doctor)
def doctor_create_prescription(request):
    if request.method == 'POST':
        form = DoctorPrescriptionForm(request.user, request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = request.user
            prescription.status = 'pending'
            prescription.save()
            messages.success(request, 'Prescription created successfully')
            return redirect('prescription:doctor_list')
    else:
        form = DoctorPrescriptionForm(doctor_user=request.user)

    return render(request, 'frontend/doctor/prescription_create.html', {'form': form})


@login_required
@user_passes_test(is_doctor)
def doctor_prescription_list(request):
    prescriptions = Prescription.objects.filter(doctor=request.user).select_related('patient', 'medicine')
    return render(request, 'frontend/doctor/prescription_list.html', {'prescriptions': prescriptions})
@login_required
@user_passes_test(is_doctor)
def doctor_trace_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk, doctor=request.user)
    batch = prescription.dispensed_batch
    manufacturer = batch.medicine.manufacturer if batch else None
    return render(request, 'frontend/doctor/prescription_trace.html', {
        'prescription': prescription,
        'batch': batch,
        'manufacturer': manufacturer,
    })


@login_required
@user_passes_test(is_pharmacist)
def pharmacist_queue(request):
    # Require patient filter: show nothing until searched
    query = (request.GET.get('q') or '').strip()
    prescriptions = []
    if query:
        filters = Q(status='pending')
        if query.isdigit():
            filters &= (Q(patient__id=int(query)) | Q(patient__national_id=query))
        else:
            filters &= (Q(patient__username__icontains=query) | Q(patient__national_id__icontains=query))
        prescriptions = (
            Prescription.objects
            .filter(filters)
            .select_related('patient', 'doctor', 'medicine')
            .order_by('-prescribed_date')
        )

    return render(request, 'frontend/pharmacist/prescription_queue.html', {
        'prescriptions': prescriptions,
        'q': query,
    })


@login_required
@user_passes_test(is_pharmacist)
def pharmacist_dispense(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)

    if request.method == 'POST':
        form = PharmacistDispenseForm(request.POST, instance=prescription, pharmacist=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status == 'dispensed':
                updated.dispensed_by = request.user
                updated.dispensed_date = timezone.now()
                # decrement stock from selected pharmacy inventory
                inv = form.cleaned_data.get('pharmacy_inventory')
                inv.current_stock -= updated.quantity
                inv.save()
                updated.dispensed_batch = inv.batch
            updated.save()
            messages.success(request, 'Prescription updated successfully')
            return redirect('prescription:pharmacist_queue')
    else:
        form = PharmacistDispenseForm(instance=prescription, pharmacist=request.user)

    return render(request, 'frontend/pharmacist/prescription_dispense.html', {
        'prescription': prescription,
        'form': form,
    })


# Patient side

@login_required
def patient_my_prescriptions(request):
    prescriptions = (
        Prescription.objects
        .filter(patient=request.user)
        .select_related('doctor', 'medicine')
        .order_by('-prescribed_date')
    )
    med_record = PatientMedicalRecord.objects.filter(patient=request.user).first()
    return render(request, 'frontend/patient/my_prescriptions.html', {
        'prescriptions': prescriptions,
        'medical_record': med_record,
    })


@login_required
def patient_history(request):
    # All prescriptions for patient, regardless of status
    prescriptions = (
        Prescription.objects
        .filter(patient=request.user)
        .select_related('doctor', 'medicine', 'dispensed_by')
        .order_by('-prescribed_date')
    )
    med_record = PatientMedicalRecord.objects.filter(patient=request.user).first()
    return render(request, 'frontend/patient/history.html', {
        'prescriptions': prescriptions,
        'medical_record': med_record,
    })


@login_required
def patient_trace_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk, patient=request.user)
    batch = prescription.dispensed_batch
    manufacturer = batch.medicine.manufacturer if batch else None
    return render(request, 'frontend/patient/prescription_trace.html', {
        'prescription': prescription,
        'batch': batch,
        'manufacturer': manufacturer,
    })


# Doctor: view patient history by username or id
@login_required
@user_passes_test(is_doctor)
def doctor_patient_history_lookup(request):
    query = (request.GET.get('q') or '').strip()
    target_patient = None
    prescriptions = []
    med_record = None
    if query:
        patient_qs = User.objects.filter(role=User.ROLE_PATIENT)
        if query.isdigit():
            patient_qs = patient_qs.filter(Q(id=int(query)) | Q(national_id=query))
        else:
            patient_qs = patient_qs.filter(Q(username__icontains=query) | Q(national_id__icontains=query))

        target_patient = patient_qs.first()
        if target_patient:
            prescriptions = (
                Prescription.objects
                .filter(patient=target_patient)
                .select_related('doctor', 'medicine', 'dispensed_by')
                .order_by('-prescribed_date')
            )
            med_record = PatientMedicalRecord.objects.filter(patient=target_patient).first()
            history_entries = PatientHistoryEntry.objects.filter(patient=target_patient).select_related('doctor')
        else:
            med_record = None
            history_entries = []
    else:
        history_entries = []

    # Create new history entry
    if request.method == 'POST' and target_patient:
        form = DoctorHistoryEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.patient = target_patient
            entry.doctor = request.user
            entry.save()
            messages.success(request, 'History entry added')
            return redirect(f"{request.path}?q={query}")
    else:
        form = DoctorHistoryEntryForm()

    return render(request, 'frontend/doctor/patient_history_lookup.html', {
        'q': query,
        'patient': target_patient,
        'prescriptions': prescriptions,
        'medical_record': med_record,
        'history_entries': history_entries,
        'form': form,
    })


# Doctor Profile Management
@login_required
@user_passes_test(is_doctor)
def doctor_profile_edit(request):
    profile, created = DoctorProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('prescription:doctor_profile_edit')
    else:
        form = DoctorProfileForm(instance=profile)
    
    return render(request, 'frontend/doctor/profile_edit.html', {'form': form, 'profile': profile})


# Messaging System
@login_required
def message_inbox(request):
    """View inbox messages"""
    received_messages = Message.objects.filter(recipient=request.user).select_related('sender').order_by('-sent_at')
    sent_messages = Message.objects.filter(sender=request.user).select_related('recipient').order_by('-sent_at')
    unread_count = received_messages.filter(is_read=False).count()
    
    return render(request, 'frontend/messaging/inbox.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'unread_count': unread_count,
    })


@login_required
def message_compose(request):
    """Compose new message"""
    if request.method == 'POST':
        form = MessageForm(sender=request.user, data=request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Message sent successfully')
            return redirect('prescription:message_inbox')
    else:
        form = MessageForm(sender=request.user)
    
    return render(request, 'frontend/messaging/compose.html', {'form': form})


@login_required
def message_detail(request, message_id):
    """View message details and reply"""
    message = get_object_or_404(Message, Q(sender=request.user) | Q(recipient=request.user), id=message_id)
    
    # Mark as read if recipient is viewing
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    
    # Get message thread (original + all replies)
    if message.parent_message:
        original = message.parent_message
    else:
        original = message
    
    thread = Message.objects.filter(
        Q(id=original.id) | Q(parent_message=original)
    ).select_related('sender', 'recipient').order_by('sent_at')
    
    if request.method == 'POST':
        form = MessageReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = message.sender if message.sender != request.user else message.recipient
            reply.subject = f"Re: {original.subject}"
            reply.parent_message = original
            reply.save()
            messages.success(request, 'Reply sent successfully')
            return redirect('prescription:message_detail', message_id=reply.id)
    else:
        form = MessageReplyForm()
    
    return render(request, 'frontend/messaging/detail.html', {
        'message': message,
        'thread': thread,
        'form': form,
    })


# Notifications
@login_required
def notification_list(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user).select_related(
        'related_prescription', 'related_message'
    ).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'frontend/notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def notification_mark_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('prescription:notification_list')


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    messages.success(request, 'All notifications marked as read')
    return redirect('prescription:notification_list')


@login_required
def get_unread_counts(request):
    """API endpoint for getting unread counts"""
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'messages': unread_messages,
        'notifications': unread_notifications,
    })


# Doctor-Patient Assignment (Admin function)
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_doctor)
def assign_doctor_to_patient(request):
    """Assign doctor to patient"""
    if request.method == 'POST':
        form = PatientDoctorAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Dr. {assignment.doctor.full_name or assignment.doctor.username} assigned to {assignment.patient.full_name or assignment.patient.username}')
            return redirect('prescription:assign_doctor_to_patient')
    else:
        form = PatientDoctorAssignmentForm()
    
    assignments = PatientDoctorAssignment.objects.all().select_related('patient', 'doctor').order_by('-assigned_date')[:50]
    
    return render(request, 'frontend/doctor/assign_patients.html', {
        'form': form,
        'assignments': assignments,
    })
