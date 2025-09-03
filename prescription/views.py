from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from authentication_app.models import User
from .models import Prescription, PatientMedicalRecord, PatientHistoryEntry
from inventory.models import PharmacyInventory
from .forms import DoctorPrescriptionForm, PharmacistDispenseForm, DoctorHistoryEntryForm


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
