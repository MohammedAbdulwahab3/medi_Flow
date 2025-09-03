import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, MedicineTransfer

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate dummy data for manufacturer side of the prescription system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of dummy records to create (default: 100)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(f'Generating {count} dummy records for manufacturer side...')
        
        # Create manufacturer users if they don't exist
        manufacturers = self.create_manufacturers()
        
        # Create medicines
        medicines = self.create_medicines(manufacturers)
        
        # Create medicine batches
        batches = self.create_batches(medicines)
        
        # Create inventory records
        inventory_items = self.create_inventory(batches)
        
        # Create medicine transfers
        transfers = self.create_transfers(batches)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'- {len(manufacturers)} manufacturer users\n'
                f'- {len(medicines)} medicines\n'
                f'- {len(batches)} medicine batches\n'
                f'- {len(inventory_items)} inventory records\n'
                f'- {len(transfers)} medicine transfers'
            )
        )

    def create_manufacturers(self):
        """Create manufacturer users"""
        manufacturers = []
        manufacturer_data = [
            {'username': 'pharma_corp', 'first_name': 'Pharma', 'last_name': 'Corp', 'license_number': 'MAN001'},
            {'username': 'med_labs', 'first_name': 'Medical', 'last_name': 'Labs', 'license_number': 'MAN002'},
            {'username': 'health_pharma', 'first_name': 'Health', 'last_name': 'Pharma', 'license_number': 'MAN003'},
            {'username': 'bio_med', 'first_name': 'Bio', 'last_name': 'Medical', 'license_number': 'MAN004'},
            {'username': 'care_pharma', 'first_name': 'Care', 'last_name': 'Pharmaceuticals', 'license_number': 'MAN005'},
        ]
        
        for data in manufacturer_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'license_number': data['license_number'],
                    'role': User.ROLE_MANUFACTURER,
                    'email': f"{data['username']}@example.com",
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created manufacturer: {user.username}')
            manufacturers.append(user)
        
        return manufacturers

    def create_medicines(self, manufacturers):
        """Create medicines"""
        medicines = []
        medicine_data = [
            # Pain relievers
            {'name': 'Paracetamol', 'generic_name': 'Acetaminophen', 'strength': '500mg', 'dosage_form': 'tablet'},
            {'name': 'Ibuprofen', 'generic_name': 'Ibuprofen', 'strength': '400mg', 'dosage_form': 'tablet'},
            {'name': 'Aspirin', 'generic_name': 'Acetylsalicylic Acid', 'strength': '100mg', 'dosage_form': 'tablet'},
            {'name': 'Diclofenac', 'generic_name': 'Diclofenac Sodium', 'strength': '50mg', 'dosage_form': 'tablet'},
            
            # Antibiotics
            {'name': 'Amoxicillin', 'generic_name': 'Amoxicillin', 'strength': '500mg', 'dosage_form': 'capsule'},
            {'name': 'Azithromycin', 'generic_name': 'Azithromycin', 'strength': '250mg', 'dosage_form': 'tablet'},
            {'name': 'Ciprofloxacin', 'generic_name': 'Ciprofloxacin', 'strength': '500mg', 'dosage_form': 'tablet'},
            {'name': 'Doxycycline', 'generic_name': 'Doxycycline', 'strength': '100mg', 'dosage_form': 'capsule'},
            
            # Cardiovascular
            {'name': 'Amlodipine', 'generic_name': 'Amlodipine Besylate', 'strength': '5mg', 'dosage_form': 'tablet'},
            {'name': 'Lisinopril', 'generic_name': 'Lisinopril', 'strength': '10mg', 'dosage_form': 'tablet'},
            {'name': 'Metformin', 'generic_name': 'Metformin Hydrochloride', 'strength': '500mg', 'dosage_form': 'tablet'},
            {'name': 'Atorvastatin', 'generic_name': 'Atorvastatin Calcium', 'strength': '20mg', 'dosage_form': 'tablet'},
            
            # Respiratory
            {'name': 'Salbutamol', 'generic_name': 'Salbutamol Sulfate', 'strength': '2mg', 'dosage_form': 'tablet'},
            {'name': 'Montelukast', 'generic_name': 'Montelukast Sodium', 'strength': '10mg', 'dosage_form': 'tablet'},
            {'name': 'Theophylline', 'generic_name': 'Theophylline', 'strength': '200mg', 'dosage_form': 'tablet'},
            
            # Gastrointestinal
            {'name': 'Omeprazole', 'generic_name': 'Omeprazole', 'strength': '20mg', 'dosage_form': 'capsule'},
            {'name': 'Ranitidine', 'generic_name': 'Ranitidine Hydrochloride', 'strength': '150mg', 'dosage_form': 'tablet'},
            {'name': 'Lansoprazole', 'generic_name': 'Lansoprazole', 'strength': '30mg', 'dosage_form': 'capsule'},
            
            # Antihistamines
            {'name': 'Cetirizine', 'generic_name': 'Cetirizine Hydrochloride', 'strength': '10mg', 'dosage_form': 'tablet'},
            {'name': 'Loratadine', 'generic_name': 'Loratadine', 'strength': '10mg', 'dosage_form': 'tablet'},
            {'name': 'Fexofenadine', 'generic_name': 'Fexofenadine Hydrochloride', 'strength': '120mg', 'dosage_form': 'tablet'},
            
            # Vitamins and Supplements
            {'name': 'Vitamin C', 'generic_name': 'Ascorbic Acid', 'strength': '500mg', 'dosage_form': 'tablet'},
            {'name': 'Vitamin D3', 'generic_name': 'Cholecalciferol', 'strength': '1000IU', 'dosage_form': 'tablet'},
            {'name': 'Calcium Carbonate', 'generic_name': 'Calcium Carbonate', 'strength': '500mg', 'dosage_form': 'tablet'},
            {'name': 'Iron Sulfate', 'generic_name': 'Ferrous Sulfate', 'strength': '325mg', 'dosage_form': 'tablet'},
            
            # Syrups
            {'name': 'Cough Syrup', 'generic_name': 'Dextromethorphan', 'strength': '15mg/5ml', 'dosage_form': 'syrup'},
            {'name': 'Multivitamin Syrup', 'generic_name': 'Multivitamin', 'strength': '5ml', 'dosage_form': 'syrup'},
            {'name': 'Iron Syrup', 'generic_name': 'Ferrous Sulfate', 'strength': '30mg/5ml', 'dosage_form': 'syrup'},
            
            # Injections
            {'name': 'Vitamin B12', 'generic_name': 'Cyanocobalamin', 'strength': '1000mcg', 'dosage_form': 'injection'},
            {'name': 'Insulin Regular', 'generic_name': 'Insulin Regular', 'strength': '100IU/ml', 'dosage_form': 'injection'},
        ]
        
        for data in medicine_data:
            manufacturer = random.choice(manufacturers)
            medicine, created = Medicine.objects.get_or_create(
                name=data['name'],
                manufacturer=manufacturer,
                defaults={
                    'generic_name': data['generic_name'],
                    'strength': data['strength'],
                    'dosage_form': data['dosage_form'],
                    'description': f"{data['generic_name']} {data['strength']} {data['dosage_form']} for therapeutic use.",
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created medicine: {medicine.name} by {manufacturer.username}')
            medicines.append(medicine)
        
        return medicines

    def create_batches(self, medicines):
        """Create medicine batches"""
        batches = []
        
        for medicine in medicines:
            # Create 2-4 batches per medicine
            num_batches = random.randint(2, 4)
            
            for i in range(num_batches):
                # Generate batch number
                batch_number = f"{medicine.name[:3].upper()}{random.randint(1000, 9999)}"
                
                # Generate dates
                manufacturing_date = date.today() - timedelta(days=random.randint(30, 365))
                expiry_date = manufacturing_date + timedelta(days=random.randint(730, 1095))  # 2-3 years
                
                # Generate quantities and prices
                quantity = random.randint(1000, 10000)
                cost_price = Decimal(random.uniform(0.5, 5.0)).quantize(Decimal('0.01'))
                selling_price = cost_price * Decimal(random.uniform(1.2, 2.0)).quantize(Decimal('0.01'))
                
                batch, created = MedicineBatch.objects.get_or_create(
                    batch_number=batch_number,
                    defaults={
                        'medicine': medicine,
                        'quantity': quantity,
                        'manufacturing_date': manufacturing_date,
                        'expiry_date': expiry_date,
                        'cost_price': cost_price,
                        'selling_price': selling_price,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(f'Created batch: {batch.batch_number} for {medicine.name}')
                batches.append(batch)
        
        return batches

    def create_inventory(self, batches):
        """Create inventory records"""
        inventory_items = []
        
        for batch in batches:
            # Calculate current stock (some batches may have been partially used)
            current_stock = random.randint(0, batch.quantity)
            reserved_stock = random.randint(0, min(current_stock, 100))
            minimum_stock_level = random.randint(10, 50)
            
            inventory, created = Inventory.objects.get_or_create(
                batch=batch,
                defaults={
                    'current_stock': current_stock,
                    'reserved_stock': reserved_stock,
                    'minimum_stock_level': minimum_stock_level,
                }
            )
            if created:
                self.stdout.write(f'Created inventory for batch: {batch.batch_number}')
            inventory_items.append(inventory)
        
        return inventory_items

    def create_transfers(self, batches):
        """Create medicine transfers"""
        transfers = []
        
        # Get pharmacists and doctors for transfers
        pharmacists = User.objects.filter(role=User.ROLE_PHARMACIST)
        doctors = User.objects.filter(role=User.ROLE_DOCTOR)
        
        # Create some pharmacists and doctors if they don't exist
        if not pharmacists.exists():
            for i in range(5):
                pharmacist = User.objects.create_user(
                    username=f'pharmacist{i+1}',
                    first_name=f'Pharmacist{i+1}',
                    last_name='Smith',
                    email=f'pharmacist{i+1}@example.com',
                    role=User.ROLE_PHARMACIST,
                    license_number=f'PHAR{i+1:03d}',
                    password='password123'
                )
                pharmacists = User.objects.filter(role=User.ROLE_PHARMACIST)
        
        if not doctors.exists():
            for i in range(5):
                doctor = User.objects.create_user(
                    username=f'doctor{i+1}',
                    first_name=f'Dr. Doctor{i+1}',
                    last_name='Johnson',
                    email=f'doctor{i+1}@example.com',
                    role=User.ROLE_DOCTOR,
                    license_number=f'DOC{i+1:03d}',
                    password='password123'
                )
                doctors = User.objects.filter(role=User.ROLE_DOCTOR)
        
        # Create transfers for batches with stock
        for batch in batches:
            if batch.inventory.current_stock > 0:
                # Create 1-3 transfers per batch
                num_transfers = random.randint(1, 3)
                
                for i in range(num_transfers):
                    # Choose recipient
                    if random.choice([True, False]):
                        to_user = random.choice(pharmacists)
                    else:
                        to_user = random.choice(doctors)
                    
                    # Transfer quantity
                    max_quantity = min(batch.inventory.current_stock, 500)
                    quantity = random.randint(10, max_quantity)
                    
                    # Transfer date
                    transfer_date = date.today() - timedelta(days=random.randint(1, 90))
                    
                    transfer = MedicineTransfer.objects.create(
                        transfer_type='manufacturer_to_pharmacy',
                        from_user=batch.medicine.manufacturer,
                        to_user=to_user,
                        batch=batch,
                        quantity=quantity,
                        transfer_date=transfer_date,
                        notes=f'Regular supply transfer of {quantity} units',
                        is_completed=True
                    )
                    
                    self.stdout.write(f'Created transfer: {quantity} units of {batch.medicine.name} to {to_user.username}')
                    transfers.append(transfer)
        
        return transfers
