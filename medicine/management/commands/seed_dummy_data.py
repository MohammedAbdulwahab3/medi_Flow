from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
import random
import string
from decimal import Decimal

from authentication_app.models import User, PharmacistProfile
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, MedicineTransfer, PharmacyInventory
from prescription.models import Prescription, PatientMedicalRecord, PatientHistoryEntry


def _rand_string(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

# Shared default password for all seeded users
DEFAULT_PASSWORD = 'password'

# Curated list of 100 common medicine generic names (approximate, for demo/seeding)
MEDICINE_NAMES = [
    'Paracetamol', 'Ibuprofen', 'Aspirin', 'Amoxicillin', 'Azithromycin', 'Ciprofloxacin', 'Metformin', 'Atorvastatin', 'Simvastatin', 'Lisinopril',
    'Losartan', 'Amlodipine', 'Omeprazole', 'Pantoprazole', 'Lansoprazole', 'Ranitidine', 'Levothyroxine', 'Insulin', 'Warfarin', 'Heparin',
    'Clopidogrel', 'Prednisone', 'Salbutamol', 'Salmeterol', 'Ipratropium', 'Montelukast', 'Cetirizine', 'Loratadine', 'Fluconazole', 'Metronidazole',
    'Doxycycline', 'Tetracycline', 'Co-trimoxazole', 'Trimethoprim', 'Amoxicillin-clavulanate', 'Cephalexin', 'Cefuroxime', 'Ceftriaxone', 'Cefixime', 'Gentamicin',
    'Vancomycin', 'Metoclopramide', 'Ondansetron', 'Loperamide', 'Furosemide', 'Spironolactone', 'Hydrochlorothiazide', 'Atenolol', 'Metoprolol', 'Propranolol',
    'Clonazepam', 'Diazepam', 'Sertraline', 'Fluoxetine', 'Escitalopram', 'Citalopram', 'Gabapentin', 'Pregabalin', 'Hydrocortisone', 'Betamethasone',
    'Clobetasol', 'Benzathine penicillin', 'Nitrofurantoin', 'Rifaximin', 'Rifampicin', 'Isoniazid', 'Ethambutol', 'Pyrazinamide', 'Oseltamivir', 'Valaciclovir',
    'Acyclovir', 'Allopurinol', 'Colchicine', 'Proton pump inhibitor (PPI)', 'Levocetirizine', 'Dexamethasone', 'Methylprednisolone', 'Sitagliptin', 'Empagliflozin', 'Saxagliptin',
    'Clarithromycin', 'Linezolid', 'Amikacin', 'Nifedipine', 'Isosorbide mononitrate', 'Nitroglycerin', 'Hydralazine', 'Methyldopa', 'Risperidone', 'Olanzapine',
    'Haloperidol', 'Donepezil', 'Memantine', 'Salicylic acid', 'Baclofen', 'Tamsulosin', 'Finasteride', 'Sildenafil', 'Tadalafil', 'Ethinylestradiol-levonorgestrel'
]

# Realistic first and last names for seeded users
FIRST_NAMES = ['Nehlla', 'Ekram', 'Mohammed', 'Amanuel', 'Sara', 'Lily', 'Hanna', 'Abebe', 'Samuel', 'Mariam', 'Teshome', 'Eden', 'Daniel', 'Getachew', 'Rahma', 'Yared', 'Belete', 'Fitsum', 'Selam', 'Kebede']
LAST_NAMES = ['Tesfaye', 'Bekele', 'Hussein', 'Kassahun', 'Gebremedhin', 'Alemu', 'Hailu', 'Wolde', 'Mengistu', 'Kebede', 'Demissie', 'Yosef', 'Tadesse', 'Fikru', 'Solomon', 'Abdisa', 'Beshah', 'Hailemariam', 'Kidane', 'Chernet']

def _gen_license():
    return f'LIC{random.randint(10000000,99999999)}'

def _gen_national_id():
    return f'NID{random.randint(1000000000,9999999999)}'


class Command(BaseCommand):
    help = 'Wipe selected app data and seed generous dummy data centered on Addis Ababa coordinates.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-wipe',
            action='store_true',
            help='Do not delete existing data before seeding',
        )
        parser.add_argument(
            '--medicines', type=int, default=100, help='Number of medicines to create'
        )
        parser.add_argument(
            '--batches-per-medicine', type=int, default=2, help='Number of batches per medicine'
        )
        parser.add_argument(
            '--pharmacies', type=int, default=5, help='Number of pharmacist/pharmacy accounts to create'
        )
        parser.add_argument(
            '--patients', type=int, default=5, help='Number of patient accounts to create'
        )
        parser.add_argument(
            '--doctors', type=int, default=5, help='Number of doctor accounts to create'
        )
        parser.add_argument(
            '--manufacturers', type=int, default=5, help='Number of manufacturer accounts to create'
        )
        parser.add_argument(
            '--prescriptions', type=int, default=400, help='Number of prescriptions to create'
        )
        parser.add_argument(
            '--keep-superuser', action='store_true', help='Keep superusers intact'
        )

    def handle(self, *args, **options):
        no_wipe = options['no_wipe']
        num_medicines = options['medicines']
        batches_per = options['batches_per_medicine']
        num_pharmacies = options['pharmacies']
        num_patients = options['patients']
        num_doctors = options['doctors']
        num_manufacturers = options['manufacturers']
        num_prescriptions = options['prescriptions']
        preserve_super = options.get('keep_superuser', False)

        # Addis Ababa center
        ADDIS_LAT = 9.03
        ADDIS_LON = 38.74

        if not no_wipe:
            self.stdout.write('Wiping existing app data (preserving superusers: {})...'.format(preserve_super))
            with transaction.atomic():
                # attempt to clear session store if using django sessions
                try:
                    from django.contrib.sessions.models import Session

                    Session.objects.all().delete()
                except Exception:
                    pass

                # attempt to clear DRF token table if present
                try:
                    from rest_framework.authtoken.models import Token

                    Token.objects.all().delete()
                except Exception:
                    pass

                Prescription.objects.all().delete()
                PatientHistoryEntry.objects.all().delete()
                PatientMedicalRecord.objects.all().delete()
                PharmacyInventory.objects.all().delete()
                Inventory.objects.all().delete()
                MedicineTransfer.objects.all().delete()
                MedicineBatch.objects.all().delete()
                Medicine.objects.all().delete()
                PharmacistProfile.objects.all().delete()

                if preserve_super:
                    User.objects.filter(is_superuser=False).delete()
                else:
                    User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Wipe complete.'))

        self.stdout.write('Seeding users...')
        manufacturers = []
        for i in range(num_manufacturers):
            dob = date.today() - timedelta(days=random.randint(25*365, 60*365))
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f'manufacturer_{i}_{_rand_string(4)}'
            u = User.objects.create_user(username=username, password=DEFAULT_PASSWORD, role=User.ROLE_MANUFACTURER, first_name=fn, last_name=ln, full_name=f'{fn} {ln}', date_of_birth=dob, phone=f'+2519{random.randint(10000000,99999999)}', address=f'{i} Industrial Rd', emergency_contact=f'+2519{random.randint(10000000,99999999)}', license_number=_gen_license(), national_id=_gen_national_id())
            manufacturers.append(u)

        doctors = []
        for i in range(num_doctors):
            dob = date.today() - timedelta(days=random.randint(30*365, 65*365))
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f'doctor_{i}_{_rand_string(4)}'
            u = User.objects.create_user(username=username, password=DEFAULT_PASSWORD, role=User.ROLE_DOCTOR, first_name=fn, last_name=ln, full_name=f'Dr. {fn} {ln}', date_of_birth=dob, phone=f'+2519{random.randint(10000000,99999999)}', address=f'{i} Clinic Rd', emergency_contact=f'+2519{random.randint(10000000,99999999)}', license_number=_gen_license(), national_id=_gen_national_id())
            doctors.append(u)

        patients = []
        for i in range(num_patients):
            dob = date.today() - timedelta(days=random.randint(10*365, 80*365))
            gender = random.choice(['male','female','other'])
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f'patient_{i}_{_rand_string(4)}'
            u = User.objects.create_user(username=username, password=DEFAULT_PASSWORD, role=User.ROLE_PATIENT, first_name=fn, last_name=ln, full_name=f'{fn} {ln}', date_of_birth=dob, gender=gender, phone=f'+2519{random.randint(10000000,99999999)}', address=f'{i} Residence Rd', emergency_contact=f'+2519{random.randint(10000000,99999999)}', national_id=_gen_national_id())
            patients.append(u)

        pharmacists = []
        for i in range(num_pharmacies):
            username = f'pharmacy_{i}_{_rand_string(4)}'
            dob = date.today() - timedelta(days=random.randint(25*365, 65*365))
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            u = User.objects.create_user(username=username, password=DEFAULT_PASSWORD, role=User.ROLE_PHARMACIST, first_name=fn, last_name=ln, full_name=f'Pharmacist {fn} {ln}', date_of_birth=dob, phone=f'+2519{random.randint(10000000,99999999)}', address=f'{i} Market St', emergency_contact=f'+2519{random.randint(10000000,99999999)}', license_number=_gen_license(), national_id=_gen_national_id())
            # create profile with Addis-centered coords (+/- 0.03 deg jitter)
            lat = round(ADDIS_LAT + random.uniform(-0.03, 0.03), 6)
            lon = round(ADDIS_LON + random.uniform(-0.03, 0.03), 6)
            prof = PharmacistProfile.objects.create(user=u, pharmacy_name=f'Pharmacy {i}', address=f'{i} Bole St', latitude=lat, longitude=lon, phone=f'+2519{random.randint(10000000,99999999)}')
            pharmacists.append((u, prof))

        self.stdout.write(self.style.SUCCESS(f'Created {len(manufacturers)} manufacturers, {len(doctors)} doctors, {len(patients)} patients, {len(pharmacists)} pharmacies'))

        self.stdout.write('Seeding medicines and batches...')
        medicines = []
        for i in range(num_medicines):
            # pick a realistic medicine name from the curated list
            med_name = MEDICINE_NAMES[i % len(MEDICINE_NAMES)]
            name = f'{med_name}'
            generic = f'{med_name} Generic'
            manufacturer = random.choice(manufacturers)
            med = Medicine.objects.create(name=name, generic_name=generic, strength=f"{random.choice([50,100,250,500])}mg", dosage_form=random.choice(['tablet','syrup','injection']), description='Seeded realistic medicine', manufacturer=manufacturer)
            medicines.append(med)
            # batches
            for b in range(batches_per):
                batch_no = f'{med.id or i}-{_rand_string(6)}'
                mfg_date = date.today() - timedelta(days=random.randint(30, 365))
                expiry = date.today() + timedelta(days=random.randint(365, 3*365))
                qty = random.randint(100, 2000)
                cost = Decimal(random.random() * 49.0 + 1.0).quantize(Decimal('0.01'))
                sell = (cost * Decimal('1.35')).quantize(Decimal('0.01'))
                mb = MedicineBatch.objects.create(medicine=med, batch_number=batch_no, quantity=qty, manufacturing_date=mfg_date, expiry_date=expiry, cost_price=cost, selling_price=sell)
                # inventory per batch
                Inventory.objects.create(batch=mb, current_stock=random.randint(0, qty), reserved_stock=random.randint(0, 10), minimum_stock_level=10)

        self.stdout.write(self.style.SUCCESS(f'Created {len(medicines)} medicines with ~{batches_per} batches each'))

        # build list of all batches for pharmacy stocking
        all_batches = list(MedicineBatch.objects.all())

        self.stdout.write('Seeding pharmacy inventories...')
        # Each pharmacy will stock a random subset of batches
        # Build objects in memory then bulk_create in chunks to avoid thousands of individual INSERTs
        ph_inv_objs = []
        for (u, prof) in pharmacists:
            k = min(len(all_batches), random.randint(20, min(200, len(all_batches))))
            chosen = random.sample(all_batches, k=k)
            for batch in chosen:
                qty = random.randint(0, 100)
                ph_inv_objs.append(PharmacyInventory(pharmacist=u, batch=batch, current_stock=qty))

        # Bulk insert in reasonable chunks. ignore_conflicts=True will skip unique_together collisions.
        CHUNK = 500
        created = 0
        with transaction.atomic():
            for i in range(0, len(ph_inv_objs), CHUNK):
                chunk = ph_inv_objs[i:i + CHUNK]
                # ignore_conflicts is available on modern Django; it performs much faster than per-row create
                PharmacyInventory.objects.bulk_create(chunk, ignore_conflicts=True)
                created += len(chunk)
                # lightweight progress feedback
                if created % (CHUNK * 2) == 0:
                    self.stdout.write(f'Inserted ~{created} pharmacy inventory rows...')

        self.stdout.write(self.style.SUCCESS('Pharmacy inventories seeded'))

        # Create some medicine transfers
        self.stdout.write('Seeding medicine transfers...')
        transfers_created = 0
        # Only manufacturer -> pharmacy transfers for seeded data
        for _ in range(max(50, num_pharmacies // 2)):
            from_user = random.choice(manufacturers)
            to_user = random.choice([u for (u,_) in pharmacists])
            batch = random.choice(all_batches)
            qty = random.randint(1, min(200, batch.quantity))
            transfer_type = 'manufacturer_to_pharmacy'
            try:
                MedicineTransfer.objects.create(transfer_type=transfer_type, from_user=from_user, to_user=to_user, batch=batch, quantity=qty, notes='Seed transfer', is_completed=True)
                transfers_created += 1
            except Exception:
                continue
        self.stdout.write(self.style.SUCCESS(f'Created {transfers_created} medicine transfers'))

        self.stdout.write('Seeding patient medical records and history entries...')
        blood_types = ['A+','A-','B+','B-','AB+','AB-','O+','O-']
        for p in patients:
            PatientMedicalRecord.objects.create(patient=p, blood_type=random.choice(blood_types), allergies='None', chronic_conditions='None', current_medications='')
            # random history entries
            for _ in range(random.randint(0,3)):
                PatientHistoryEntry.objects.create(patient=p, doctor=random.choice(doctors), case_summary='Routine check', diagnosis='-', treatment_plan='Rest', notes='Generated')

        self.stdout.write(self.style.SUCCESS('Patient records seeded'))

        self.stdout.write('Seeding prescriptions...')
        meds_for_prescribe = medicines if medicines else list(Medicine.objects.all())
        for _ in range(num_prescriptions):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            med = random.choice(meds_for_prescribe)
            qty = random.randint(1, 30)
            pres = Prescription.objects.create(patient=patient, doctor=doctor, medicine=med, dosage=f'{random.randint(1,2)} tablets', duration=f'{random.randint(1,14)} days', quantity=qty, notes='Generated by seed script')
            # randomly mark some dispensed
            if random.random() < 0.2:
                pres.status = 'dispensed'
                pres.dispensed_by = random.choice([u for (u,_) in pharmacists])
                pres.dispensed_date = date.today()
                # optionally link a dispensed batch
                batch = random.choice(all_batches)
                pres.dispensed_batch = batch
                pres.save()

        self.stdout.write(self.style.SUCCESS(f'Created {num_prescriptions} prescriptions'))

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
