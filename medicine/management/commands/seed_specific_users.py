from django.core.management.base import BaseCommand
from datetime import date, timedelta

from authentication_app.models import User, PharmacistProfile, ManufacturerProfile
from prescription.models import PatientMedicalRecord, DoctorProfile


class Command(BaseCommand):
    help = 'Create specific demo users: Ekram (patient), Mohammed (manufacturer), Nehla (pharmacist), Mahi (doctor) with minimal realistic profiles.'

    def add_arguments(self, parser):
        parser.add_argument('--full', action='store_true', help='Also wipe non-user data and seed medicines, batches, inventories, transfers and prescriptions')

    def handle(self, *args, **options):
        # Patient: Ekram
        ekram_data = {
            'username': 'ekram',
            'first_name': 'Ekram',
            'last_name': 'Khedir',
            'full_name': 'Ekram Khedir',
            'role': User.ROLE_PATIENT,
            'email': 'ekram@example.com',
            'phone': '+251911000001',
            'address': 'Addis Ababa, Ethiopia',
            'national_id': 'NID-EKRAM-0001',
        }
        ekram, created = User.objects.update_or_create(username=ekram_data['username'], defaults=ekram_data)
        if created:
            ekram.set_password('password')
            ekram.save()
        self.stdout.write(self.style.SUCCESS(f'Patient Ekram: user={ekram.username} created/updated'))

        # Ensure PatientMedicalRecord exists
        pmr, _ = PatientMedicalRecord.objects.get_or_create(patient=ekram, defaults={'blood_type': 'O+', 'allergies': 'None', 'chronic_conditions': 'None'})
        self.stdout.write(self.style.SUCCESS(f'Patient medical record for Ekram ensured'))

        # Manufacturer: Mohammed
        mohammed_data = {
            'username': 'mohammed',
            'first_name': 'Mohammed',
            'last_name': 'Abdulwahab',
            'full_name': 'Mohammed Abdulwahab',
            'role': User.ROLE_MANUFACTURER,
            'email': 'mohammed@example.com',
            'phone': '+251911000002',
            'address': 'Addis Ababa, Ethiopia',
            'license_number': 'LIC-MOH-0001',
            'national_id': 'NID-MOH-0002',
        }
        mohammed, created = User.objects.update_or_create(username=mohammed_data['username'], defaults=mohammed_data)
        if created:
            mohammed.set_password('password')
            mohammed.save()
        self.stdout.write(self.style.SUCCESS(f'Manufacturer Mohammed: user={mohammed.username} created/updated'))

        # ManufacturerProfile (guarded in case migrations not applied)
        try:
            manuf_profile, _ = ManufacturerProfile.objects.update_or_create(user=mohammed, defaults={
                'company_name': 'maw Pharma Ltd',
                'address': 'Addis Ababa, Ethiopia',
                'phone': mohammed.phone,
                'contact_email': 'contact@mawpharma.example',
                'website': '',
            })
            self.stdout.write(self.style.SUCCESS('Manufacturer profile ensured'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped ManufacturerProfile creation (possible unapplied migrations): {e}'))

        # Pharmacist: Nehla
        nehla_data = {
            'username': 'nehla',
            'first_name': 'Nehla',
            'last_name': 'Khedir',
            'full_name': 'Nehla Khedir',
            'role': User.ROLE_PHARMACIST,
            'email': 'nehla@example.com',
            'phone': '+251911000003',
            'address': 'Addis Ababa, Ethiopia',
            'license_number': 'LIC-NEH-0001',
            'national_id': 'NID-NEH-0003',
        }
        nehla, created = User.objects.update_or_create(username=nehla_data['username'], defaults=nehla_data)
        if created:
            nehla.set_password('password')
            nehla.save()
        self.stdout.write(self.style.SUCCESS(f'Pharmacist Nehla: user={nehla.username} created/updated'))

        # PharmacistProfile (guarded)
        try:
            phil, _ = PharmacistProfile.objects.update_or_create(user=nehla, defaults={
                'pharmacy_name': "Nehla's Pharmacy",
                'address': 'Addis Ababa, Ethiopia',
                'phone': nehla.phone,
                'latitude': 9.03,
                'longitude': 38.74,
            })
            self.stdout.write(self.style.SUCCESS('Pharmacist profile ensured'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped PharmacistProfile creation (possible unapplied migrations): {e}'))

        # Doctor: Mahi
        mahi_data = {
            'username': 'mahi',
            'first_name': 'Mahi',
            'last_name': 'seid',
            'full_name': 'Dr. Mahi seid',
            'role': User.ROLE_DOCTOR,
            'email': 'mahi@example.com',
            'phone': '+251911000004',
            'address': 'Addis Ababa, Ethiopia',
            'license_number': 'LIC-MAH-0001',
            'national_id': 'NID-MAH-0004',
        }
        mahi, created = User.objects.update_or_create(username=mahi_data['username'], defaults=mahi_data)
        if created:
            mahi.set_password('password')
            mahi.save()
        self.stdout.write(self.style.SUCCESS(f'Doctor Mahi: user={mahi.username} created/updated'))

        # DoctorProfile (guarded)
        try:
            doc_profile, _ = DoctorProfile.objects.update_or_create(user=mahi, defaults={
                'specialization': 'General Practitioner',
                'qualifications': 'MD',
                'years_of_experience': 5,
                'consultation_fee': 300.00,
                'available_days': 'Mon-Fri',
                'available_hours': '9AM-5PM',
            })
            self.stdout.write(self.style.SUCCESS('Doctor profile ensured'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Skipped DoctorProfile creation (possible unapplied migrations): {e}'))

        self.stdout.write(self.style.SUCCESS('All specific demo users created/updated. Password for all users is "password" (change it in production).'))
        # If --full was passed, also seed medicines and related models
        if options.get('full'):
            self.stdout.write('Full seed requested: wiping non-user data and seeding demo models...')
            from medicine.models import Medicine, MedicineBatch
            from inventory.models import Inventory, PharmacyInventory, MedicineTransfer, ReservationRequest
            from prescription.models import Prescription
            # wipe models except users
            try:
                ReservationRequest.objects.all().delete()
            except Exception:
                pass
            try:
                MedicineTransfer.objects.all().delete()
            except Exception:
                pass
            try:
                PharmacyInventory.objects.all().delete()
            except Exception:
                pass
            try:
                Inventory.objects.all().delete()
            except Exception:
                pass
            try:
                MedicineBatch.objects.all().delete()
            except Exception:
                pass
            try:
                Medicine.objects.all().delete()
            except Exception:
                pass
            try:
                Prescription.objects.all().delete()
            except Exception:
                pass

            # seed a small set of medicines and batches
            med_names = ['Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Omeprazole']
            meds = []
            manufacturers = list(User.objects.filter(role=User.ROLE_MANUFACTURER))
            pharmacists = list(User.objects.filter(role=User.ROLE_PHARMACIST))
            for i, name in enumerate(med_names):
                m = Medicine.objects.create(name=name, generic_name=f'{name} Generic', strength='500mg', dosage_form='tablet', manufacturer=manufacturers[0] if manufacturers else None, description='Seeded')
                meds.append(m)
                mb = MedicineBatch.objects.create(medicine=m, batch_number=f'SEED-{i}', quantity=500, manufacturing_date=date.today(), expiry_date=date.today()+timedelta(days=365), cost_price=1.0, selling_price=1.5)
                try:
                    Inventory.objects.create(batch=mb, current_stock=500, reserved_stock=0, minimum_stock_level=10)
                except Exception:
                    pass

            # seed pharmacy inventories
            all_batches = list(MedicineBatch.objects.all())
            for p in pharmacists:
                for batch in all_batches[:2]:
                    try:
                        PharmacyInventory.objects.create(pharmacist=p, batch=batch, current_stock=10, selling_price=batch.selling_price)
                    except Exception:
                        pass

            # seed a couple of transfers
            for _ in range(3):
                if not manufacturers or not pharmacists or not all_batches:
                    break
                try:
                    MedicineTransfer.objects.create(transfer_type='manufacturer_to_pharmacy', from_user=manufacturers[0], to_user=pharmacists[0], batch=all_batches[0], quantity=5, notes='Seed transfer', is_completed=True)
                except Exception:
                    pass

            # seed a few prescriptions
            patients = list(User.objects.filter(role=User.ROLE_PATIENT))
            doctors = list(User.objects.filter(role=User.ROLE_DOCTOR))
            for _ in range(10):
                if not patients or not doctors or not meds:
                    break
                try:
                    Prescription.objects.create(patient=random.choice(patients), doctor=random.choice(doctors), medicine=random.choice(meds), dosage='1 tablet', duration='7 days', quantity=5, notes='Seeded')
                except Exception:
                    pass

            self.stdout.write(self.style.SUCCESS('Full seeding complete.'))
