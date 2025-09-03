import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from prescription.models import PatientMedicalRecord, Prescription, PatientHistoryEntry
from authentication_app.models import User as UserModel
from medicine.models import Medicine


FIRST_NAMES = [
    'Liam','Noah','Oliver','Elijah','James','William','Benjamin','Lucas','Henry','Theodore',
    'Olivia','Emma','Ava','Sophia','Isabella','Mia','Charlotte','Amelia','Harper','Evelyn'
]
LAST_NAMES = ['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez']
BLOOD_TYPES = ['A+','A-','B+','B-','AB+','AB-','O+','O-']
ALLERGIES = ['Penicillin','Peanuts','Shellfish','Latex','None','Dust','Pollen','Eggs','Milk','Bee stings']
CHRONIC = ['Hypertension','Diabetes','Asthma','None','Hypothyroidism','Arthritis']
SURGERIES = ['Appendectomy','C-section','Tonsillectomy','Gallbladder removal','None']


class Command(BaseCommand):
    help = 'Seed 50 dummy patients with medical records and some prescriptions'

    def handle(self, *args, **options):
        User = get_user_model()

        # Ensure at least one doctor exists
        doctor, _ = User.objects.get_or_create(
            username='doctor_demo',
            defaults={'role': UserModel.ROLE_DOCTOR, 'email': 'doctor@example.com'}
        )
        doctor.set_password('password123')
        doctor.save()

        # Ensure at least one medicine exists
        medicine = Medicine.objects.first()
        if not medicine:
            self.stdout.write(self.style.WARNING('No Medicine found. Please create at least one medicine for demo prescriptions.'))

        created = 0
        for i in range(50):
            username = f"patient{i+1}"
            patient, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'role': UserModel.ROLE_PATIENT,
                    'email': f'{username}@example.com'
                }
            )
            patient.set_password('password123')
            patient.save()

            PatientMedicalRecord.objects.update_or_create(
                patient=patient,
                defaults={
                    'blood_type': random.choice(BLOOD_TYPES),
                    'allergies': random.choice(ALLERGIES),
                    'chronic_conditions': random.choice(CHRONIC),
                    'past_surgeries': random.choice(SURGERIES),
                    'current_medications': 'Ibuprofen 200mg PRN',
                    'family_history': 'Father: Hypertension; Mother: None',
                    'social_history': 'Non-smoker; occasional exercise',
                    'notes': 'Generated for demo',
                }
            )

            # Optionally create a few prescriptions
            if medicine:
                for _ in range(random.randint(0, 3)):
                    Prescription.objects.create(
                        patient=patient,
                        doctor=doctor,
                        medicine=medicine,
                        dosage='1 tablet BID',
                        duration='7 days',
                        quantity=random.randint(5, 20),
                        status=random.choice(['pending', 'dispensed', 'cancelled'])
                    )

            # Create some history entries authored by random doctors (using doctor_demo here)
            for _ in range(random.randint(1, 3)):
                PatientHistoryEntry.objects.create(
                    patient=patient,
                    doctor=doctor,
                    case_summary=random.choice([
                        'Routine checkup', 'Follow-up visit', 'Flu-like symptoms', 'Headache and nausea', 'Back pain'
                    ]),
                    diagnosis=random.choice(['Viral infection', 'Migraine', 'Muscle strain', 'Undiagnosed']),
                    treatment_plan=random.choice([
                        'Rest and hydration', 'Analgesics PRN', 'Physiotherapy referral', 'Observation'
                    ]),
                    notes='Auto-generated demo entry'
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} patients with medical records.'))


