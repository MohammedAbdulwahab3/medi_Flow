from rest_framework import serializers
from authentication_app.models import User
from prescription.models import Prescription, PatientMedicalRecord
from medicine.models import Medicine, MedicineBatch


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'uuid', 'first_name', 'last_name', 'email', 'role']


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientMedicalRecord
        fields = ['blood_type', 'allergies', 'chronic_conditions', 'current_medications', 'last_updated']


class MedicineMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'generic_name', 'strength', 'dosage_form']


class PrescriptionSerializer(serializers.ModelSerializer):
    medicine = MedicineMiniSerializer(read_only=True)
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = ['id', 'patient', 'doctor', 'medicine', 'dosage', 'duration', 'quantity', 'prescribed_date', 'status', 'notes', 'dispensed_date']


class MedicineDetailSerializer(serializers.ModelSerializer):
    batches = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = ['id', 'name', 'generic_name', 'strength', 'dosage_form', 'description', 'manufacturer', 'batches']

    def get_batches(self, obj):
        qs = MedicineBatch.objects.filter(medicine=obj, is_active=True).order_by('expiry_date')[:5]
        return [{'batch_number': b.batch_number, 'expiry_date': b.expiry_date, 'quantity': b.quantity, 'is_expired': b.is_expired} for b in qs]


class MedicineListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'generic_name', 'strength', 'dosage_form', 'is_active']


class PharmacyAvailabilitySerializer(serializers.Serializer):
    pharmacy_name = serializers.CharField()
    pharmacist_username = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    current_stock = serializers.IntegerField()
