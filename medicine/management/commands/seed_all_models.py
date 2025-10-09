from django.core.management.base import BaseCommand
from django.core.management import call_command
from datetime import date, timedelta
import random
from decimal import Decimal

from django.contrib.auth import get_user_model

from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, PharmacyInventory, MedicineTransfer, ReservationRequest
from prescription.models import Prescription, PatientMedicalRecord, PatientHistoryEntry, DoctorProfile
from authentication_app.models import PharmacistProfile, ManufacturerProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Wipe data (except preserved users) and seed users + medicines + inventory + transfers + prescriptions.'

    def add_arguments(self, parser):
        parser.add_argument('--no-wipe', action='store_true', help='Do not delete existing data')
        parser.add_argument('--preserve-users', type=str, default='ekram,mohammed,nehla,mahi', help='Comma-separated usernames to keep')
        parser.add_argument('--keep-superuser', action='store_true', help='Preserve superusers')
        parser.add_argument('--medicines', type=int, default=30)
        parser.add_argument('--batches-per-medicine', dest='batches_per_medicine', type=int, default=1)
        parser.add_argument('--pharmacies', type=int, default=3)
        parser.add_argument('--patients', type=int, default=5)
        parser.add_argument('--doctors', type=int, default=3)
        parser.add_argument('--manufacturers', type=int, default=3)
        parser.add_argument('--prescriptions', type=int, default=50)

    def handle(self, *args, **options):
        no_wipe = options['no_wipe']
        preserve_users = [u.strip() for u in options['preserve_users'].split(',') if u.strip()]
        keep_super = options['keep_superuser']

        self.stdout.write('Preserve users: %s (keep_superuser=%s)' % (preserve_users, keep_super))

        if not no_wipe:
            self.stdout.write('Wiping data (this will keep preserved users)...')

            # delete many models explicitly to keep control
            model_qs_list = [
                ReservationRequest.objects.all(),
                MedicineTransfer.objects.all(),
                PharmacyInventory.objects.all(),
                Inventory.objects.all(),
                MedicineBatch.objects.all(),
                Medicine.objects.all(),
                Prescription.objects.all(),
                PatientHistoryEntry.objects.all(),
                PatientMedicalRecord.objects.all(),
                DoctorProfile.objects.all(),
                PharmacistProfile.objects.all(),
                ManufacturerProfile.objects.all(),
            ]
            for qs in model_qs_list:
                try:
                    qs.delete()
                except Exception:
                    continue

            # delete users except preserved
            users_qs = User.objects.all()
            if preserve_users:
                users_qs = users_qs.exclude(username__in=preserve_users)
            if keep_super:
                users_qs = users_qs.exclude(is_superuser=True)
            users_qs.delete()

            self.stdout.write(self.style.SUCCESS('Wipe complete.'))

        # Ensure preserved users and their profiles exist by calling seed_specific_users
        self.stdout.write('Ensuring preserved specific users exist...')
        try:
            call_command('seed_specific_users')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to run seed_specific_users: {e}'))

        # Now seed other demo data
        num_medicines = options['medicines']
        batches_per = options.get('batches_per_medicine', 1)
        num_pharmacies = options['pharmacies']
        num_patients = options['patients']
        num_doctors = options['doctors']
        num_manufacturers = options['manufacturers']
        num_prescriptions = options['prescriptions']

        # gather current users for roles
        manufacturers = list(User.objects.filter(role=User.ROLE_MANUFACTURER))
        pharmacists = list(User.objects.filter(role=User.ROLE_PHARMACIST))
        doctors = list(User.objects.filter(role=User.ROLE_DOCTOR))
        patients = list(User.objects.filter(role=User.ROLE_PATIENT))

        # create additional role users if counts not met
        def create_users_for_role(role, target_count, username_prefix):
            existing = list(User.objects.filter(role=role))
            created = []
            i = 0
            while len(existing) + len(created) < target_count:
                uname = f"{username_prefix}_{i}_{random.randint(1000,9999)}"
                u = User.objects.create_user(username=uname, password='password', role=role, first_name=username_prefix.title(), last_name=str(i), full_name=f"{username_prefix.title()} {i}", phone='+251900000000', address='Addis Ababa, Ethiopia')
                created.append(u)
                i += 1
            return existing + created

        if len(manufacturers) < num_manufacturers:
            manufacturers = create_users_for_role(User.ROLE_MANUFACTURER, num_manufacturers, 'manufacturer')
        if len(pharmacists) < num_pharmacies:
            pharmacists = create_users_for_role(User.ROLE_PHARMACIST, num_pharmacies, 'pharmacy')
        if len(doctors) < num_doctors:
            doctors = create_users_for_role(User.ROLE_DOCTOR, num_doctors, 'doctor')
        if len(patients) < num_patients:
            patients = create_users_for_role(User.ROLE_PATIENT, num_patients, 'patient')

        self.stdout.write(self.style.SUCCESS(f'Users prepared: manufacturers={len(manufacturers)}, pharmacists={len(pharmacists)}, doctors={len(doctors)}, patients={len(patients)}'))

        # Seed medicines and batches
        self.stdout.write('Seeding medicines and batches...')
        med_names = [
            'Paracetamol', 'Ibuprofen', 'Amoxicillin', 'Omeprazole', 'Metformin', 'Atorvastatin', 'Salbutamol', 'Cetirizine', 'Insulin', 'Amlodipine'
        ]

        medicines = []
        for i in range(num_medicines):
            name = med_names[i % len(med_names)] + (f' {i}' if i >= len(med_names) else '')
            manufacturer = random.choice(manufacturers) if manufacturers else None
            med = Medicine.objects.create(name=name, generic_name=f'{name} Generic', strength='500mg', dosage_form='tablet', manufacturer=manufacturer, description='Seeded medicine')
            medicines.append(med)
            for b in range(batches_per):
                batch_no = f'{med.id or i}-{random.randint(10000,99999)}'
                mfg_date = date.today() - timedelta(days=random.randint(30, 365))
                expiry = date.today() + timedelta(days=random.randint(365, 3*365))
                qty = random.randint(100, 1000)
                cost = Decimal(random.random() * 20.0 + 1.0).quantize(Decimal('0.01'))
                sell = (cost * Decimal('1.4')).quantize(Decimal('0.01'))
                mb = MedicineBatch.objects.create(medicine=med, batch_number=batch_no, quantity=qty, manufacturing_date=mfg_date, expiry_date=expiry, cost_price=cost, selling_price=sell)
                try:
                    Inventory.objects.create(batch=mb, current_stock=random.randint(0, qty), reserved_stock=0, minimum_stock_level=10)
                except Exception:
                    # inventory may not have warehouse field in older schema; ignore
                    continue

        self.stdout.write(self.style.SUCCESS(f'Created {len(medicines)} medicines with {batches_per} batches each'))

        # Seed pharmacy inventories (pharmacists stock random batches)
        self.stdout.write('Seeding pharmacy inventories...')
        all_batches = list(MedicineBatch.objects.all())
        for p in pharmacists:
            if not all_batches:
                break
            chosen = random.sample(all_batches, k=min(len(all_batches), max(5, random.randint(5, 20))))
            for batch in chosen:
                try:
                    PharmacyInventory.objects.create(pharmacist=p, batch=batch, current_stock=random.randint(0, 50), selling_price=batch.selling_price)
                except Exception:
                    continue

        # Seed some transfers
        self.stdout.write('Seeding transfers...')
        for _ in range(max(10, len(pharmacists))):
            if not manufacturers or not pharmacists or not all_batches:
                break
            from_user = random.choice(manufacturers)
            to_user = random.choice(pharmacists)
            batch = random.choice(all_batches)
            qty = random.randint(1, min(50, batch.quantity))
            try:
                MedicineTransfer.objects.create(transfer_type='manufacturer_to_pharmacy', from_user=from_user, to_user=to_user, batch=batch, quantity=qty, notes='Seed transfer', is_completed=True)
            except Exception:
                continue

        # Seed prescriptions
        self.stdout.write('Seeding prescriptions...')
        for _ in range(num_prescriptions):
            if not patients or not doctors or not medicines:
                break
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            med = random.choice(medicines)
            qty = random.randint(1, 30)
            try:
                pres = Prescription.objects.create(patient=patient, doctor=doctor, medicine=med, dosage='1 tablet', duration='7 days', quantity=qty, notes='Seeded prescription')
            except Exception:
                continue
            if random.random() < 0.2 and PharmacyInventory.objects.exists():
                try:
                    pres.status = 'dispensed'
                    pres.dispensed_by = random.choice(pharmacists)
                    pres.dispensed_date = date.today()
                    pres.dispensed_batch = random.choice(all_batches)
                    pres.save()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from datetime import date, timedelta
import random
from decimal import Decimal

from django.contrib.auth import get_user_model

from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, PharmacyInventory, MedicineTransfer, ReservationRequest
from prescription.models import Prescription, PatientMedicalRecord, PatientHistoryEntry, DoctorProfile
from authentication_app.models import PharmacistProfile, ManufacturerProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Wipe data (except preserved users) and seed users + medicines + inventory + transfers + prescriptions.'

    def add_arguments(self, parser):
        parser.add_argument('--no-wipe', action='store_true', help='Do not delete existing data')
        parser.add_argument('--preserve-users', type=str, default='ekram,mohammed,nehla,mahi', help='Comma-separated usernames to keep')
        parser.add_argument('--keep-superuser', action='store_true', help='Preserve superusers')
        parser.add_argument('--medicines', type=int, default=30)
        parser.add_argument('--batches-per-medicine', type=int, default=1)
        parser.add_argument('--pharmacies', type=int, default=3)
        parser.add_argument('--patients', type=int, default=5)
        parser.add_argument('--doctors', type=int, default=3)
        parser.add_argument('--manufacturers', type=int, default=3)
        parser.add_argument('--prescriptions', type=int, default=50)

    def handle(self, *args, **options):
        no_wipe = options['no_wipe']
        preserve_users = [u.strip() for u in options['preserve_users'].split(',') if u.strip()]
        keep_super = options['keep_superuser']

        self.stdout.write('Preserve users: %s (keep_superuser=%s)' % (preserve_users, keep_super))

        if not no_wipe:
            self.stdout.write('Wiping data (this will keep preserved users)...')
            with transaction.atomic():
                # delete many models explicitly to keep control
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
                try:
                    PatientHistoryEntry.objects.all().delete()
                except Exception:
                    pass
                try:
                    PatientMedicalRecord.objects.all().delete()
                except Exception:
                    pass
                try:
                    DoctorProfile.objects.all().delete()
                except Exception:
                    pass
                try:
                    PharmacistProfile.objects.all().delete()
                except Exception:
                    pass
                try:
                    ManufacturerProfile.objects.all().delete()
                except Exception:
                    pass

                # delete users except preserved
                users_qs = User.objects.all()
                if preserve_users:
                    users_qs = users_qs.exclude(username__in=preserve_users)
                if keep_super:
                    users_qs = users_qs.exclude(is_superuser=True)
                users_qs.delete()

            self.stdout.write(self.style.SUCCESS('Wipe complete.'))

        # Ensure preserved users and their profiles exist by calling seed_specific_users
        self.stdout.write('Ensuring preserved specific users exist...')
        try:
            call_command('seed_specific_users')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to run seed_specific_users: {e}'))

        # Now seed other demo data
        num_medicines = options['medicines']
        batches_per = options['batches_per_medicine']
        num_pharmacies = options['pharmacies']
        num_patients = options['patients']
        num_doctors = options['doctors']
        num_manufacturers = options['manufacturers']
        num_prescriptions = options['prescriptions']

        # gather current users for roles
        manufacturers = list(User.objects.filter(role=User.ROLE_MANUFACTURER))
        pharmacists = list(User.objects.filter(role=User.ROLE_PHARMACIST))
        doctors = list(User.objects.filter(role=User.ROLE_DOCTOR))
        patients = list(User.objects.filter(role=User.ROLE_PATIENT))

        # create additional role users if counts not met
        def create_users_for_role(role, target_count, username_prefix):
            existing = list(User.objects.filter(role=role))
            created = []
            i = 0
            while len(existing) + len(created) < target_count:
                uname = f"{username_prefix}_{i}_{random.randint(1000,9999)}"
                u = User.objects.create_user(username=uname, password='password', role=role, first_name=username_prefix.title(), last_name=str(i), full_name=f"{username_prefix.title()} {i}", phone='+251900000000', address='Addis Ababa, Ethiopia')
                created.append(u)
                i += 1
            return existing + created

        if len(manufacturers) < num_manufacturers:
            manufacturers = create_users_for_role(User.ROLE_MANUFACTURER, num_manufacturers, 'manufacturer')
        if len(pharmacists) < num_pharmacies:
            pharmacists = create_users_for_role(User.ROLE_PHARMACIST, num_pharmacies, 'pharmacy')
        if len(doctors) < num_doctors:
            doctors = create_users_for_role(User.ROLE_DOCTOR, num_doctors, 'doctor')
                # delete many models explicitly to keep control
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
                try:
                    PatientHistoryEntry.objects.all().delete()
                except Exception:
                    pass
                try:
                    PatientMedicalRecord.objects.all().delete()
                except Exception:
                    pass
                try:
                    DoctorProfile.objects.all().delete()
                except Exception:
                    pass
                try:
                    PharmacistProfile.objects.all().delete()
                except Exception:
                    pass
                try:
                    ManufacturerProfile.objects.all().delete()
                except Exception:
                    pass

                # delete users except preserved
        self.stdout.write('Seeding prescriptions...')
        for _ in range(num_prescriptions):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            med = random.choice(medicines)
            qty = random.randint(1, 30)
            pres = Prescription.objects.create(patient=patient, doctor=doctor, medicine=med, dosage='1 tablet', duration='7 days', quantity=qty, notes='Seeded prescription')
            if random.random() < 0.2 and PharmacyInventory.objects.exists():
                pres.status = 'dispensed'
                pres.dispensed_by = random.choice(pharmacists)
                pres.dispensed_date = date.today()
                pres.dispensed_batch = random.choice(all_batches)
                pres.save()

    self.stdout.write(self.style.SUCCESS('Seeding complete.'))
