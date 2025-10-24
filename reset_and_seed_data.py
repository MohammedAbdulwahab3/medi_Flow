#!/usr/bin/env python
"""
Complete seed script for MediFlow project.

Save as seed_data.py in the project root (same directory as manage.py).
Run: python seed_data.py
"""

import os
import sys
import django
from datetime import datetime
import random

# Add project root to path (assumes script placed next to manage.py)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medi_flow.settings')
django.setup()

from django.contrib.auth import get_user_model
from authentication_app.models import ManufacturerProfile, PharmacistProfile
from medicine.models import Medicine, MedicineBatch
from inventory.models import Warehouse, Inventory
from prescription.models import DoctorProfile, PatientMedicalRecord
from django.db import transaction

UserModel = get_user_model()


def _parse_date(date_str):
    """Parse YYYY-MM-DD to datetime.date, or return None if blank."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def create_superuser():
    """Create or update admin user"""
    print("Creating superuser...")
    if UserModel.objects.filter(username='admin').exists():
        admin = UserModel.objects.get(username='admin')
        admin.email = 'admin@mediflow.com'
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        admin.role = 'admin'
        admin.save()
        print("Admin user updated (already existed).")
        return admin

    superuser = UserModel.objects.create_superuser(
        username='admin',
        email='admin@mediflow.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print("Superuser created: admin")
    return superuser


def create_manufacturers():
    """Create 5 manufacturers with Ethiopian details"""
    print("Creating manufacturers...")
    manufacturers_data = [
        {
            'username': 'ethiopharma',
            'email': 'info@ethiopharma.com.et',
            'password': 'manufacturer123',
            'first_name': 'Mohammed',
            'last_name': 'Ahmed',
            'role': 'manufacturer',
            'company_name': 'EthioPharma PLC',
            'address': 'Addis Ababa, Bole District',
            'phone': '+251 11 123 4567',
            'website': 'https://www.ethiopharma.com.et',
            'contact_email': 'contact@ethiopharma.com.et',
            'license_number': 'MFG-001-ETH',
            'latitude': 9.0300,
            'longitude': 38.7400
        },
        {
            'username': 'himalayapharma',
            'email': 'info@himalayapharma.com.et',
            'password': 'manufacturer123',
            'first_name': 'Ekram',
            'last_name': 'Hassan',
            'role': 'manufacturer',
            'company_name': 'Himalaya Pharmaceuticals',
            'address': 'Addis Ababa, Kirkos District',
            'phone': '+251 11 234 5678',
            'website': 'https://www.himalayapharma.com.et',
            'contact_email': 'info@himalayapharma.com.et',
            'license_number': 'MFG-002-ETH',
            'latitude': 9.0200,
            'longitude': 38.7500
        },
        {
            'username': 'africanmeds',
            'email': 'info@africanmeds.com.et',
            'password': 'manufacturer123',
            'first_name': 'Frawol',
            'last_name': 'Tesfaye',
            'role': 'manufacturer',
            'company_name': 'African Medical Supplies',
            'address': 'Addis Ababa, Arada District',
            'phone': '+251 11 345 6789',
            'website': 'https://www.africanmeds.com.et',
            'contact_email': 'support@africanmeds.com.et',
            'license_number': 'MFG-003-ETH',
            'latitude': 9.0400,
            'longitude': 38.7300
        },
        {
            'username': 'medsupplyeth',
            'email': 'info@medsupplyeth.com.et',
            'password': 'manufacturer123',
            'first_name': 'Tesnim',
            'last_name': 'Abdi',
            'role': 'manufacturer',
            'company_name': 'Medical Supply Ethiopia',
            'address': 'Addis Ababa, Nifas Silk District',
            'phone': '+251 11 456 7890',
            'website': 'https://www.medsupplyeth.com.et',
            'contact_email': 'orders@medsupplyeth.com.et',
            'license_number': 'MFG-004-ETH',
            'latitude': 9.0500,
            'longitude': 38.7200
        },
        {
            'username': 'healthcareeth',
            'email': 'info@healthcareeth.com.et',
            'password': 'manufacturer123',
            'first_name': 'Biruk',
            'last_name': 'Kebede',
            'role': 'manufacturer',
            'company_name': 'Healthcare Solutions Ethiopia',
            'address': 'Addis Ababa, Kolfe Keranio District',
            'phone': '+251 11 567 8901',
            'website': 'https://www.healthcareeth.com.et',
            'contact_email': 'service@healthcareeth.com.et',
            'license_number': 'MFG-005-ETH',
            'latitude': 9.0100,
            'longitude': 38.7600
        }
    ]

    created = []
    for data in manufacturers_data:
        if UserModel.objects.filter(username=data['username']).exists():
            user = UserModel.objects.get(username=data['username'])
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.role = 'manufacturer'
            user.address = data['address']
            user.phone = data['phone']
            user.license_number = data['license_number']
            user.save()
            print(f"Updated manufacturer user: {user.username}")
        else:
            user = UserModel.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role='manufacturer',
                address=data['address'],
                phone=data['phone'],
                license_number=data['license_number']
            )
            print(f"Created manufacturer user: {user.username}")

        profile, _ = ManufacturerProfile.objects.get_or_create(
            user=user,
            defaults={
                'company_name': data['company_name'],
                'address': data['address'],
                'phone': data['phone'],
                'website': data['website'],
                'contact_email': data['contact_email']
            }
        )
        profile.company_name = data['company_name']
        profile.address = data['address']
        profile.phone = data['phone']
        profile.website = data['website']
        profile.contact_email = data['contact_email']
        if hasattr(profile, 'latitude'):
            profile.latitude = data.get('latitude')
        if hasattr(profile, 'longitude'):
            profile.longitude = data.get('longitude')
        profile.save()

        created.append(user)

    return created


def create_pharmacists():
    """Create 5 pharmacists"""
    print("Creating pharmacists...")
    pharmacists_data = [
        {
            'username': 'pharmamohammed',
            'email': 'mohammed@pharma.com.et',
            'password': 'pharmacist123',
            'first_name': 'Mohammed',
            'last_name': 'Ali',
            'role': 'pharmacist',
            'pharmacy_name': 'City Central Pharmacy',
            'address': 'Addis Ababa, Bole Road',
            'phone': '+251 11 111 2222',
            'license_number': 'PHR-001-ETH',
            'latitude': 9.0300,
            'longitude': 38.7400
        },
        {
            'username': 'pharmaekram',
            'email': 'ekram@pharma.com.et',
            'password': 'pharmacist123',
            'first_name': 'Ekram',
            'last_name': 'Omar',
            'role': 'pharmacist',
            'pharmacy_name': 'University Pharmacy',
            'address': 'Addis Ababa, University District',
            'phone': '+251 11 222 3333',
            'license_number': 'PHR-002-ETH',
            'latitude': 9.0200,
            'longitude': 38.7500
        },
        {
            'username': 'pharmafrawol',
            'email': 'frawol@pharma.com.et',
            'password': 'pharmacist123',
            'first_name': 'Frawol',
            'last_name': 'Girma',
            'role': 'pharmacist',
            'pharmacy_name': 'St. Mary Pharmacy',
            'address': 'Addis Ababa, Piassa',
            'phone': '+251 11 333 4444',
            'license_number': 'PHR-003-ETH',
            'latitude': 9.0400,
            'longitude': 38.7300
        },
        {
            'username': 'pharmatesnim',
            'email': 'tesnim@pharma.com.et',
            'password': 'pharmacist123',
            'first_name': 'Tesnim',
            'last_name': 'Yimer',
            'role': 'pharmacist',
            'pharmacy_name': 'Green Cross Pharmacy',
            'address': 'Addis Ababa, Merkato',
            'phone': '+251 11 444 5555',
            'license_number': 'PHR-004-ETH',
            'latitude': 9.0500,
            'longitude': 38.7200
        },
        {
            'username': 'pharmabiruk',
            'email': 'biruk@pharma.com.et',
            'password': 'pharmacist123',
            'first_name': 'Biruk',
            'last_name': 'Lemma',
            'role': 'pharmacist',
            'pharmacy_name': 'MediCare Pharmacy',
            'address': 'Addis Ababa, CMC',
            'phone': '+251 11 555 6666',
            'license_number': 'PHR-005-ETH',
            'latitude': 9.0100,
            'longitude': 38.7600
        }
    ]

    created = []
    for data in pharmacists_data:
        if UserModel.objects.filter(username=data['username']).exists():
            user = UserModel.objects.get(username=data['username'])
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.role = 'pharmacist'
            user.address = data['address']
            user.phone = data['phone']
            user.license_number = data['license_number']
            user.save()
            print(f"Updated pharmacist: {user.username}")
        else:
            user = UserModel.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role='pharmacist',
                address=data['address'],
                phone=data['phone'],
                license_number=data['license_number']
            )
            print(f"Created pharmacist: {user.username}")

        profile, _ = PharmacistProfile.objects.get_or_create(
            user=user,
            defaults={
                'pharmacy_name': data['pharmacy_name'],
                'address': data['address'],
                'phone': data['phone']
            }
        )
        profile.pharmacy_name = data['pharmacy_name']
        profile.address = data['address']
        profile.phone = data['phone']
        if hasattr(profile, 'latitude'):
            profile.latitude = data.get('latitude')
        if hasattr(profile, 'longitude'):
            profile.longitude = data.get('longitude')
        profile.save()

        created.append(user)

    return created


def create_doctors():
    """Create 3 doctors with Ethiopian details"""
    print("Creating doctors...")
    doctors_data = [
        {
            'username': 'dr_mohammed',
            'email': 'mohammed@hospital.com.et',
            'password': 'doctor123',
            'first_name': 'Mohammed',
            'last_name': 'Hussen',
            'role': 'doctor',
            'specialization': 'General Medicine',
            'qualifications': 'MBBS, MD',
            'years_of_experience': 10,
            'consultation_fee': 500.00,
            'license_number': 'DOC-001-ETH'
        },
        {
            'username': 'dr_ekram',
            'email': 'ekram@hospital.com.et',
            'password': 'doctor123',
            'first_name': 'Ekram',
            'last_name': 'Mahmoud',
            'role': 'doctor',
            'specialization': 'Pediatrics',
            'qualifications': 'MBBS, DCH',
            'years_of_experience': 8,
            'consultation_fee': 600.00,
            'license_number': 'DOC-002-ETH'
        },
        {
            'username': 'dr_frawol',
            'email': 'frawol@hospital.com.et',
            'password': 'doctor123',
            'first_name': 'Frawol',
            'last_name': 'Abebe',
            'role': 'doctor',
            'specialization': 'Cardiology',
            'qualifications': 'MBBS, DM Cardiology',
            'years_of_experience': 12,
            'consultation_fee': 800.00,
            'license_number': 'DOC-003-ETH'
        }
    ]

    created = []
    for data in doctors_data:
        if UserModel.objects.filter(username=data['username']).exists():
            user = UserModel.objects.get(username=data['username'])
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.role = 'doctor'
            user.license_number = data['license_number']
            user.save()
            print(f"Updated doctor user: {user.username}")
        else:
            user = UserModel.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role='doctor',
                license_number=data['license_number']
            )
            print(f"Created doctor user: {user.username}")

        profile, _ = DoctorProfile.objects.get_or_create(
            user=user,
            defaults={
                'specialization': data['specialization'],
                'qualifications': data['qualifications'],
                'years_of_experience': data['years_of_experience'],
                'consultation_fee': data['consultation_fee']
            }
        )
        profile.specialization = data['specialization']
        profile.qualifications = data['qualifications']
        profile.years_of_experience = data['years_of_experience']
        profile.consultation_fee = data['consultation_fee']
        profile.save()

        created.append(user)

    return created


def create_patients():
    """Create 10 patients with full medical records (idempotent)"""
    print("Creating patients...")

    medical_fields_samples = [
        {
            "past_surgeries": "Appendectomy (2010)",
            "current_medications": "Lisinopril, Atorvastatin",
            "family_history": "Father: coronary artery disease; Mother: type 2 diabetes",
            "social_history": "Non-smoker; drinks alcohol socially; primary school teacher; lives with spouse",
            "notes": "Penicillin allergy (rash). Recent elevated BP; follow-up in 4 weeks."
        },
        {
            "past_surgeries": "Cesarean section (2016); Laparoscopic cholecystectomy (2020)",
            "current_medications": "Levothyroxine",
            "family_history": "Mother: hypothyroidism; Maternal grandfather: stroke",
            "social_history": "Never smoker; no alcohol; sedentary job (office admin)",
            "notes": "Pregnancy history G2P1; wants contraception counseling."
        },
        {
            "past_surgeries": "Left knee arthroscopy (2018)",
            "current_medications": "Ibuprofen PRN; Vitamin D supplement",
            "family_history": "No known hereditary conditions",
            "social_history": "Former smoker (10 pack-years, quit 2019); occasional cannabis; construction worker",
            "notes": "Intermittent knee pain with stairs — refer to physiotherapy."
        },
        {
            "past_surgeries": "None",
            "current_medications": "Metformin, Glimepiride",
            "family_history": "Strong family history of diabetes (both parents)",
            "social_history": "Smoker (15 cigarettes/day); drinks alcohol weekly; lives with extended family",
            "notes": "Recent HbA1c elevated; dietary counseling recommended."
        },
        {
            "past_surgeries": "CABG (coronary artery bypass) 2015",
            "current_medications": "Aspirin, Atorvastatin, Bisoprolol",
            "family_history": "Father died age 62 of MI; siblings with HTN",
            "social_history": "Does not smoke; avoids alcohol; retired",
            "notes": "Cardiology follow-up due; monitors INR not required (on aspirin)."
        },
        {
            "past_surgeries": "Hysterectomy (2012)",
            "current_medications": "Albuterol inhaler PRN",
            "family_history": "Mother: asthma; Father: hypertension",
            "social_history": "Non-smoker; works part-time in retail; dog owner",
            "notes": "Asthma well-controlled; review inhaler technique at next visit."
        },
        {
            "past_surgeries": "Total hip replacement (right) 2021",
            "current_medications": "Warfarin (anticoagulation)",
            "family_history": "Sibling: DVT history",
            "social_history": "Former light smoker; no alcohol; uses cane at home",
            "notes": "Regular INR checks required; provide warfarin education and interaction list."
        },
        {
            "past_surgeries": "Tonsillectomy (childhood)",
            "current_medications": "Levothyroxine; Sertraline",
            "family_history": "Mother: depression",
            "social_history": "Non-smoker; drinks alcohol rarely; college student",
            "notes": "Screen for medication adherence; reports insomnia — review sleep hygiene."
        },
        {
            "past_surgeries": "Left rotator cuff repair (2019)",
            "current_medications": "None regular; topical NSAID PRN",
            "family_history": "No significant history",
            "social_history": "Smoker (5 cigarettes/day); occasional alcohol; gym-goer",
            "notes": "Physical therapy completed; occasional shoulder stiffness after heavy lifting."
        },
        {
            "past_surgeries": "Appendix removed (childhood); Emergency exploratory laparotomy (2014)",
            "current_medications": "Levetiracetam (for seizure disorder)",
            "family_history": "Uncle with epilepsy",
            "social_history": "Does not smoke; lives alone; works as taxi driver; irregular sleep",
            "notes": "Seizure-free for 18 months; advised to avoid sleep deprivation and to carry medical ID."
        }
    ]

    patients_base = [
        {'username': 'patient_tesnim', 'email': 'tesnim@gmail.com', 'password': 'patient123', 'first_name': 'Tesnim', 'last_name': 'Mohammed', 'address': 'Addis Ababa, Bole', 'phone': '+251911111111', 'date_of_birth': '1990-05-15', 'gender': 'female', 'blood_type': 'O+', 'allergies': 'Penicillin, Peanuts', 'chronic_conditions': 'Asthma', 'license_number': 'PAT-001-ETH'},
        {'username': 'patient_biruk', 'email': 'biruk@gmail.com', 'password': 'patient123', 'first_name': 'Biruk', 'last_name': 'Alemu', 'address': 'Addis Ababa, Kirkos', 'phone': '+251911222222', 'date_of_birth': '1985-12-03', 'gender': 'male', 'blood_type': 'A+', 'allergies': 'None', 'chronic_conditions': 'Hypertension', 'license_number': 'PAT-002-ETH'},
        {'username': 'patient_ahmed', 'email': 'ahmed@gmail.com', 'password': 'patient123', 'first_name': 'Ahmed', 'last_name': 'Hassan', 'address': 'Addis Ababa, Arada', 'phone': '+251911333333', 'date_of_birth': '1995-08-22', 'gender': 'male', 'blood_type': 'B+', 'allergies': 'Dust, Pollen', 'chronic_conditions': 'Diabetes Type 2', 'license_number': 'PAT-003-ETH'},
        {'username': 'patient_saba', 'email': 'saba@gmail.com', 'password': 'patient123', 'first_name': 'Saba', 'last_name': 'Kebede', 'address': 'Addis Ababa, Merkato', 'phone': '+251911444444', 'date_of_birth': '1992-03-10', 'gender': 'female', 'blood_type': 'AB+', 'allergies': 'Sulfa', 'chronic_conditions': 'None', 'license_number': 'PAT-004-ETH'},
        {'username': 'patient_yared', 'email': 'yared@gmail.com', 'password': 'patient123', 'first_name': 'Yared', 'last_name': 'Tadesse', 'address': 'Addis Ababa, CMC', 'phone': '+251911555555', 'date_of_birth': '1978-11-02', 'gender': 'male', 'blood_type': 'O-', 'allergies': 'None', 'chronic_conditions': 'Hyperlipidemia', 'license_number': 'PAT-005-ETH'},
        {'username': 'patient_elen', 'email': 'elen@gmail.com', 'password': 'patient123', 'first_name': 'Elen', 'last_name': 'Bekele', 'address': 'Addis Ababa, Arada', 'phone': '+251911666666', 'date_of_birth': '1988-07-21', 'gender': 'female', 'blood_type': 'A-', 'allergies': 'Peanuts', 'chronic_conditions': 'Hypothyroidism', 'license_number': 'PAT-006-ETH'},
        {'username': 'patient_habtemu', 'email': 'habtemu@gmail.com', 'password': 'patient123', 'first_name': 'Habtemu', 'last_name': 'Gebremedhin', 'address': 'Addis Ababa, Bole', 'phone': '+251911777777', 'date_of_birth': '1965-04-12', 'gender': 'male', 'blood_type': 'B-', 'allergies': 'None', 'chronic_conditions': 'AF (Atrial Fibrillation)', 'license_number': 'PAT-007-ETH'},
        {'username': 'patient_martha', 'email': 'martha@gmail.com', 'password': 'patient123', 'first_name': 'Martha', 'last_name': 'Yohannes', 'address': 'Addis Ababa, Kirkos', 'phone': '+251911888888', 'date_of_birth': '2000-09-09', 'gender': 'female', 'blood_type': 'AB-', 'allergies': 'Latex', 'chronic_conditions': 'Depression', 'license_number': 'PAT-008-ETH'},
        {'username': 'patient_samuel', 'email': 'samuel@gmail.com', 'password': 'patient123', 'first_name': 'Samuel', 'last_name': 'Wolde', 'address': 'Addis Ababa, Nifas Silk', 'phone': '+251911999999', 'date_of_birth': '1993-02-14', 'gender': 'male', 'blood_type': 'O+', 'allergies': 'Dust', 'chronic_conditions': 'Seizure disorder', 'license_number': 'PAT-009-ETH'},
        {'username': 'patient_fikir', 'email': 'fikir@gmail.com', 'password': 'patient123', 'first_name': 'Fikir', 'last_name': 'Mekonnen', 'address': 'Addis Ababa, Kolfe', 'phone': '+251911101010', 'date_of_birth': '1980-06-30', 'gender': 'female', 'blood_type': 'B+', 'allergies': 'None', 'chronic_conditions': 'Osteoarthritis', 'license_number': 'PAT-010-ETH'},
    ]

    created = []
    for base, med in zip(patients_base, medical_fields_samples):
        data = {**base, **med}
        username = data['username']

        with transaction.atomic():
            if UserModel.objects.filter(username=username).exists():
                user = UserModel.objects.get(username=username)
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.email = data['email']
                user.role = 'patient'
                user.address = data.get('address', '')
                user.phone = data.get('phone', '')
                try:
                    if data.get('date_of_birth'):
                        user.date_of_birth = datetime.strptime(data['date_of_birth'], "%Y-%m-%d").date()
                except Exception:
                    pass
                user.gender = data.get('gender', '')
                user.license_number = data.get('license_number', '')
                user.save()
                print(f"Updated patient user: {user.username}")
            else:
                kwargs = {
                    'username': data['username'],
                    'email': data['email'],
                    'password': data['password'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'patient',
                    'address': data.get('address', ''),
                    'phone': data.get('phone', ''),
                    'license_number': data.get('license_number', '')
                }
                try:
                    kwargs['date_of_birth'] = datetime.strptime(data['date_of_birth'], "%Y-%m-%d").date()
                except Exception:
                    pass
                try:
                    kwargs['gender'] = data.get('gender', '')
                except Exception:
                    pass

                user = UserModel.objects.create_user(**kwargs)
                print(f"Created patient user: {user.username}")

            pmr_defaults = {
                'blood_type': data.get('blood_type'),
                'allergies': data.get('allergies', ''),
                'chronic_conditions': data.get('chronic_conditions', ''),
                'past_surgeries': data.get('past_surgeries', ''),
                'current_medications': data.get('current_medications', ''),
                'family_history': data.get('family_history', ''),
                'social_history': data.get('social_history', ''),
                'notes': data.get('notes', '')
            }
            record, created_record = PatientMedicalRecord.objects.get_or_create(
                patient=user,
                defaults=pmr_defaults
            )
            if not created_record:
                for k, v in pmr_defaults.items():
                    if v is not None:
                        setattr(record, k, v)
                record.save()

            created.append(user)

    return created


def create_medicines(manufacturers):
    """Create 15 medicines, batches and inventory (safe/idempotent)
    IMAGE URLs preserved exactly as provided by you.
    """
    print("Creating medicines...")

    m0 = manufacturers[0] if len(manufacturers) > 0 else None
    m1 = manufacturers[1] if len(manufacturers) > 1 else m0
    m2 = manufacturers[2] if len(manufacturers) > 2 else m0
    m3 = manufacturers[3] if len(manufacturers) > 3 else m0
    m4 = manufacturers[4] if len(manufacturers) > 4 else m0

    medicines_data = [
        {
            'name': 'Paracetamol',
            'generic_name': 'Acetaminophen',
            'strength': '500mg',
            'dosage_form': 'tablet',
            'category': 'pain_relief',
            'description': 'Paracetamol is a common painkiller used to treat aches and pains and reduce fever.',
            'image': 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.eurekadirect.co.uk%2FMedical-Consumables%2FPharmaceuticals%2FParacetamol-500mg&psig=AOvVaw15QCAT2h5yYZaMTqklYuS1&ust=1760430384797000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCMid_7DgoJADFQAAAAAdAAAAABAE',
            'manufacturer': m0,
            'cost_price': 2.50,
            'selling_price': 5.00,
            'quantity': 1000,
            'batch_number': 'PAR001',
            'manufacturing_date': '2025-01-15',
            'expiry_date': '2027-01-15',
            'status': 'normal'
        },
        {
            'name': 'Amoxicillin',
            'generic_name': 'Amoxicillin',
            'strength': '250mg',
            'dosage_form': 'capsule',
            'category': 'antibiotics',
            'description': 'Amoxicillin is used to treat a wide variety of bacterial infections.',
            'image': 'https://plus.unsplash.com/premium_photo-1668446396677-375c13da7e7d?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8QW1veGljaWxsaW58ZW58MHx8MHx8fDA%3D&auto=format&fit=crop&q=60&w=600',
            'manufacturer': m1,
            'cost_price': 8.00,
            'selling_price': 15.00,
            'quantity': 0,
            'batch_number': 'AMX001',
            'manufacturing_date': '2025-02-20',
            'expiry_date': '2027-02-20',
            'status': 'out_of_stock'
        },
        {
            'name': 'Ibuprofen',
            'generic_name': 'Ibuprofen',
            'strength': '400mg',
            'dosage_form': 'tablet',
            'category': 'pain_relief',
            'description': 'Ibuprofen is an NSAID used to reduce pain, swelling, and fever.',
            'image': 'https://images.unsplash.com/photo-1550572017-4fcdbb59cc32?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8SWJ1cHJvZmVufGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=600',
            'manufacturer': m2,
            'cost_price': 3.50,
            'selling_price': 7.00,
            'quantity': 5,
            'batch_number': 'IBU001',
            'manufacturing_date': '2025-03-10',
            'expiry_date': '2027-03-10',
            'status': 'near_out_of_stock'
        },
        {
            'name': 'Ciprofloxacin',
            'generic_name': 'Ciprofloxacin',
            'strength': '500mg',
            'dosage_form': 'tablet',
            'category': 'antibiotics',
            'description': 'Ciprofloxacin is a fluoroquinolone antibiotic used to treat bacterial infections.',
            'image': 'https://images.unsplash.com/photo-1729708273852-b63222c8b35d?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8Q2lwcm9mbG94YWNpbnxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&q=60&w=600',
            'manufacturer': m3,
            'cost_price': 12.00,
            'selling_price': 22.00,
            'quantity': 300,
            'batch_number': 'CIP001',
            'manufacturing_date': '2024-01-30',
            'expiry_date': '2024-07-30',
            'status': 'expired'
        },
        {
            'name': 'Lisinopril',
            'generic_name': 'Lisinopril',
            'strength': '10mg',
            'dosage_form': 'tablet',
            'category': 'cardiovascular',
            'description': 'Lisinopril is an ACE inhibitor used to treat high blood pressure and heart failure.',
            'image': 'https://unsplash.com/photos/a-jar-of-peanut-butter-on-a-bed-MjLxJVfU6hw',
            'manufacturer': m4,
            'cost_price': 6.50,
            'selling_price': 12.00,
            'quantity': 400,
            'batch_number': 'LIS001',
            'manufacturing_date': '2025-02-15',
            'expiry_date': '2027-02-15',
            'status': 'normal'
        },
        {
            'name': 'Metformin',
            'generic_name': 'Metformin',
            'strength': '500mg',
            'dosage_form': 'tablet',
            'category': 'diabetes',
            'description': 'Metformin is used to control high blood sugar in people with type 2 diabetes.',
            'image': 'https://images.unsplash.com/photo-1616526629705-981c263b68bc?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8TWV0Zm9ybWlufGVufDB8fDB8fHww&auto=format&fit=crop&q=60&w=600',
            'manufacturer': m0,
            'cost_price': 4.00,
            'selling_price': 8.00,
            'quantity': 600,
            'batch_number': 'MET001',
            'manufacturing_date': '2025-03-05',
            'expiry_date': '2025-09-05',
            'status': 'near_expiration'
        },
        {
            'name': 'Atorvastatin',
            'generic_name': 'Atorvastatin',
            'strength': '20mg',
            'dosage_form': 'tablet',
            'category': 'cardiovascular',
            'description': 'Atorvastatin lowers cholesterol and triglycerides to reduce the risk of heart disease.',
            'image': 'https://media.istockphoto.com/id/1343227833/photo/generic-box-and-blister-pack-of-atorvastatin-tablets.webp?a=1&b=1&s=612x612&w=0&k=20&c=v0lSrfV_YgVaC3IPRK_QQYGUr2CLlVkLTutYHnacyII=',
            'manufacturer': m1,
            'cost_price': 9.00,
            'selling_price': 18.00,
            'quantity': 350,
            'batch_number': 'ATO001',
            'manufacturing_date': '2025-01-25',
            'expiry_date': '2027-01-25',
            'status': 'normal'
        },
        {
            'name': 'Omeprazole',
            'generic_name': 'Omeprazole',
            'strength': '20mg',
            'dosage_form': 'capsule',
            'category': 'gastrointestinal',
            'description': 'Omeprazole treats conditions caused by too much stomach acid.',
            'image': 'https://plus.unsplash.com/premium_photo-1726750812399-215ecdc98235?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8T21lcHJhem9sZXxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&q=60&w=600',
            'manufacturer': m2,
            'cost_price': 5.50,
            'selling_price': 11.00,
            'quantity': 0,
            'batch_number': 'OME001',
            'manufacturing_date': '2025-02-28',
            'expiry_date': '2027-02-28',
            'status': 'out_of_stock'
        },
        {
            'name': 'Salbutamol',
            'generic_name': 'Albuterol',
            'strength': '100mcg',
            'dosage_form': 'inhaler',
            'category': 'respiratory',
            'description': 'Salbutamol is a short-acting bronchodilator used to treat asthma.',
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCSg3QE4v3n75DPJrfDHxXtCVJ9ABRsIOuMQ&s',
            'manufacturer': m3,
            'cost_price': 15.00,
            'selling_price': 28.00,
            'quantity': 200,
            'batch_number': 'SAL001',
            'manufacturing_date': '2025-03-12',
            'expiry_date': '2027-03-12',
            'status': 'normal'
        },
        {
            'name': 'Diazepam',
            'generic_name': 'Diazepam',
            'strength': '5mg',
            'dosage_form': 'tablet',
            'category': 'other',
            'description': 'Diazepam is used to treat anxiety, alcohol withdrawal, and seizures.',
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSkg1VRHSSeky4pAuJu66GyGFxCm0c3YmcvCg&s',
            'manufacturer': m4,
            'cost_price': 7.50,
            'selling_price': 14.00,
            'quantity': 10,
            'batch_number': 'DIA001',
            'manufacturing_date': '2025-01-20',
            'expiry_date': '2027-01-20',
            'status': 'near_out_of_stock'
        },
        {
            'name': 'Levothyroxine',
            'generic_name': 'Levothyroxine',
            'strength': '50mcg',
            'dosage_form': 'tablet',
            'category': 'other',
            'description': 'Levothyroxine is a synthetic thyroid hormone used for hypothyroidism.',
            'image': 'https://yaralpharma.com/wp-content/uploads/2023/06/Levothyroxine-box-and-blister-1024x958.jpg',
            'manufacturer': m0,
            'cost_price': 6.00,
            'selling_price': 12.00,
            'quantity': 450,
            'batch_number': 'LEV001',
            'manufacturing_date': '2023-02-10',
            'expiry_date': '2024-02-10',
            'status': 'expired'
        },
        {
            'name': 'Aspirin',
            'generic_name': 'Acetylsalicylic Acid',
            'strength': '325mg',
            'dosage_form': 'tablet',
            'category': 'pain_relief',
            'description': 'Aspirin reduces fever and relieves mild to moderate pain.',
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6lsxO7_OtfVFgcgBv_hK7mMcjCO_pXEp7HA&s',
            'manufacturer': m1,
            'cost_price': 3.00,
            'selling_price': 6.00,
            'quantity': 900,
            'batch_number': 'ASP001',
            'manufacturing_date': '2025-03-08',
            'expiry_date': '2027-03-08',
            'status': 'normal'
        },
        {
            'name': 'Cetirizine',
            'generic_name': 'Cetirizine',
            'strength': '10mg',
            'dosage_form': 'tablet',
            'category': 'other',
            'description': 'Cetirizine relieves allergy symptoms.',
            'image': 'https://thehealthpharmacy.co.uk/wp-content/uploads/2024/02/cetirizine.jpg',
            'manufacturer': m2,
            'cost_price': 4.50,
            'selling_price': 9.00,
            'quantity': 550,
            'batch_number': 'CET001',
            'manufacturing_date': '2025-01-18',
            'expiry_date': '2025-07-18',
            'status': 'near_expiration'
        },
        {
            'name': 'Diclofenac',
            'generic_name': 'Diclofenac',
            'strength': '50mg',
            'dosage_form': 'tablet',
            'category': 'pain_relief',
            'description': 'Diclofenac is an NSAID used to treat pain and inflammation.',
            'image': 'https://wonneinternational.com/wp-content/uploads/2022/10/Dicovan-Aqua.jpeg',
            'manufacturer': m3,
            'cost_price': 5.00,
            'selling_price': 10.00,
            'quantity': 650,
            'batch_number': 'DIC001',
            'manufacturing_date': '2025-02-22',
            'expiry_date': '2027-02-22',
            'status': 'normal'
        },
        {
            'name': 'Ranitidine',
            'generic_name': 'Ranitidine',
            'strength': '150mg',
            'dosage_form': 'tablet',
            'category': 'gastrointestinal',
            'description': 'Ranitidine reduces the amount of acid produced by the stomach.',
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRXjiTkr2R9I-BbqHsjim01EblkkgNSBu9MKw&s',
            'manufacturer': m4,
            'cost_price': 6.50,
            'selling_price': 13.00,
            'quantity': 3,
            'batch_number': 'RAN001',
            'manufacturing_date': '2025-03-03',
            'expiry_date': '2027-03-03',
            'status': 'near_out_of_stock'
        }
    ]

    created = []
    for data in medicines_data:
        if not data.get('manufacturer'):
            print(f"Skipping medicine {data['name']} because manufacturer not available.")
            continue

        med_qs = Medicine.objects.filter(name=data['name'], manufacturer=data['manufacturer'])
        if med_qs.exists():
            med = med_qs.first()
            med.generic_name = data['generic_name']
            med.strength = data['strength']
            med.dosage_form = data['dosage_form']
            med.category = data['category']
            med.description = data['description']
            med.image = data['image']
            med.manufacturer = data['manufacturer']
            med.save()
            print(f"Updated medicine: {med.name}")
        else:
            med = Medicine.objects.create(
                name=data['name'],
                generic_name=data['generic_name'],
                strength=data['strength'],
                dosage_form=data['dosage_form'],
                category=data['category'],
                description=data['description'],
                image=data['image'],
                manufacturer=data['manufacturer']
            )
            print(f"Created medicine: {med.name}")

        mfg_date = _parse_date(data.get('manufacturing_date'))
        exp_date = _parse_date(data.get('expiry_date'))
        batch_qs = MedicineBatch.objects.filter(batch_number=data['batch_number'])
        if batch_qs.exists():
            batch = batch_qs.first()
            batch.medicine = med
            batch.quantity = data['quantity']
            if mfg_date:
                batch.manufacturing_date = mfg_date
            if exp_date:
                batch.expiry_date = exp_date
            batch.cost_price = data['cost_price']
            batch.selling_price = data['selling_price']
            batch.save()
            print(f"Updated batch: {batch.batch_number} for {med.name}")
        else:
            batch = MedicineBatch.objects.create(
                medicine=med,
                batch_number=data['batch_number'],
                quantity=data['quantity'],
                manufacturing_date=mfg_date,
                expiry_date=exp_date,
                cost_price=data['cost_price'],
                selling_price=data['selling_price']
            )
            print(f"Created batch: {batch.batch_number} for {med.name}")

        try:
            manufacturer_profile = data['manufacturer'].manufacturer_profile
            warehouse_name = f"Main Warehouse - {manufacturer_profile.company_name}"
            warehouse, _ = Warehouse.objects.get_or_create(
                manufacturer=data['manufacturer'],
                name=warehouse_name,
                defaults={'address': manufacturer_profile.address or data['manufacturer'].address, 'is_primary': True}
            )
            warehouse.address = manufacturer_profile.address or warehouse.address
            warehouse.is_primary = True
            warehouse.save()
        except Exception:
            warehouse, _ = Warehouse.objects.get_or_create(
                manufacturer=data['manufacturer'],
                name=f"Main Warehouse - {data['manufacturer'].username}",
                defaults={'address': data['manufacturer'].address or '', 'is_primary': True}
            )

        inv_qs = Inventory.objects.filter(batch=batch)
        if inv_qs.exists():
            inv = inv_qs.first()
            inv.current_stock = data['quantity']
            inv.warehouse = warehouse
            inv.save()
            print(f"Updated inventory for batch {batch.batch_number}")
        else:
            Inventory.objects.create(batch=batch, current_stock=data['quantity'], warehouse=warehouse)
            print(f"Created inventory for batch {batch.batch_number}")

        created.append(med)

    return created


def main():
    print("=" * 60)
    print("RUNNING MEDIFLOW DATA SEEDER")
    print("=" * 60)

    try:
        superuser = create_superuser()
        manufacturers = create_manufacturers()
        pharmacists = create_pharmacists()
        doctors = create_doctors()
        patients = create_patients()
        medicines = create_medicines(manufacturers)

        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"Superuser: {superuser.username} / admin123")
        print(f"Manufacturers: {len(manufacturers)}")
        print(f"Pharmacists: {len(pharmacists)}")
        print(f"Doctors: {len(doctors)}")
        print(f"Patients: {len(patients)}")
        print(f"Medicines: {len(medicines)}")
    except Exception as e:
        print("Seeding failed:", str(e))
        raise


if __name__ == '__main__':
    main()
