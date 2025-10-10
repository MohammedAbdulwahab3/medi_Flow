#!/usr/bin/env python
"""
Script to create test notifications and messages for the patient app
Run this to populate the database with test data
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medi_flow.settings')
django.setup()

from authentication_app.models import User
from prescription.models import Notification, Message, Prescription, PatientDoctorAssignment
from medicine.models import Medicine
from django.utils import timezone

def create_test_data():
    """Create test notifications and messages for patient users"""
    
    # Get or create a patient user
    try:
        patient_user = User.objects.get(username='patient1')
        print(f"Found existing patient user: {patient_user.username}")
    except User.DoesNotExist:
        # Create a test patient user
        patient_user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='password123',
            first_name='John',
            last_name='Doe',
            role='patient'
        )
        print(f"Created new patient user: {patient_user.username}")
    
    # Get or create a doctor user for sending messages
    try:
        doctor_user = User.objects.get(username='doctor1')
    except User.DoesNotExist:
        doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='password123',
            first_name='Dr. Sarah',
            last_name='Smith',
            role='doctor'
        )
        print(f"Created doctor user: {doctor_user.username}")
    
    # Create test notifications
    notifications_data = [
        {
            'notification_type': 'prescription_created',
            'title': 'New Prescription Available',
            'message': 'Dr. Smith has prescribed Amoxicillin 500mg for you. Please collect it from the pharmacy.',
            'is_read': False,
        },
        {
            'notification_type': 'appointment_reminder',
            'title': 'Appointment Reminder',
            'message': 'You have an appointment with Dr. Smith tomorrow at 2:00 PM.',
            'is_read': False,
        },
        {
            'notification_type': 'prescription_dispensed',
            'title': 'Prescription Dispensed',
            'message': 'Your prescription for Ibuprofen has been dispensed at City Pharmacy.',
            'is_read': True,
        },
        {
            'notification_type': 'doctor_assigned',
            'title': 'New Doctor Assigned',
            'message': 'Dr. Johnson has been assigned as your primary care physician.',
            'is_read': False,
        },
        {
            'notification_type': 'message_received',
            'title': 'New Message from Doctor',
            'message': 'You have received a new message from Dr. Smith regarding your treatment.',
            'is_read': False,
        }
    ]
    
    # Delete existing notifications for this user to avoid duplicates
    Notification.objects.filter(user=patient_user).delete()
    
    created_notifications = []
    for notif_data in notifications_data:
        notification = Notification.objects.create(
            user=patient_user,
            **notif_data
        )
        created_notifications.append(notification)
        print(f"Created notification: {notification.title}")
    
    # Create test messages
    messages_data = [
        {
            'subject': 'Prescription Instructions',
            'body': 'Please take your medication with food and drink plenty of water. If you experience any side effects, contact me immediately.',
            'is_read': False,
        },
        {
            'subject': 'Lab Results Available',
            'body': 'Your recent lab results are now available. Overall, everything looks good. We should schedule a follow-up appointment next month.',
            'is_read': False,
        },
        {
            'subject': 'Appointment Confirmation',
            'body': 'This is to confirm your appointment on Friday, October 15th at 10:30 AM. Please arrive 15 minutes early.',
            'is_read': True,
        },
        {
            'subject': 'Medication Refill',
            'body': 'Your prescription for blood pressure medication is due for refill. Please contact the pharmacy or schedule an appointment.',
            'is_read': False,
        }
    ]
    
    # Delete existing messages for this user to avoid duplicates
    Message.objects.filter(recipient=patient_user).delete()
    
    created_messages = []
    for msg_data in messages_data:
        message = Message.objects.create(
            sender=doctor_user,
            recipient=patient_user,
            **msg_data
        )
        created_messages.append(message)
        print(f"Created message: {message.subject}")
    
    # Get or create a manufacturer user
    try:
        manufacturer_user = User.objects.get(username='manufacturer1')
    except User.DoesNotExist:
        manufacturer_user = User.objects.create_user(
            username='manufacturer1',
            email='manufacturer1@example.com',
            password='password123',
            first_name='PharmaCorp',
            last_name='Ltd',
            role='manufacturer'
        )
        print(f"Created manufacturer user: {manufacturer_user.username}")
    
    # Create a test prescription if none exists
    try:
        # Get or create a test medicine
        medicine, created = Medicine.objects.get_or_create(
            name='Amoxicillin',
            defaults={
                'generic_name': 'Amoxicillin',
                'strength': '500mg',
                'dosage_form': 'tablet',
                'description': 'Antibiotic medication for bacterial infections',
                'manufacturer': manufacturer_user,
                'category': 'antibiotics'
            }
        )
        if created:
            print(f"Created medicine: {medicine.name}")
        
        # Create test prescription
        prescription, created = Prescription.objects.get_or_create(
            patient=patient_user,
            doctor=doctor_user,
            medicine=medicine,
            defaults={
                'dosage': '500mg twice daily',
                'duration': '7 days',
                'quantity': 30,
                'status': 'pending',
                'notes': 'Take with food'
            }
        )
        if created:
            print(f"Created prescription: {prescription}")
        
    except Exception as e:
        print(f"Error creating prescription: {e}")
    
    # Create doctor assignment
    try:
        assignment, created = PatientDoctorAssignment.objects.get_or_create(
            patient=patient_user,
            doctor=doctor_user,
            defaults={
                'is_primary': True,
                'notes': 'Primary care physician assignment'
            }
        )
        if created:
            print(f"Created doctor assignment: {assignment}")
    except Exception as e:
        print(f"Error creating doctor assignment: {e}")
    
    # Print summary
    print("\n" + "="*50)
    print("TEST DATA CREATION SUMMARY")
    print("="*50)
    print(f"Patient User: {patient_user.username} ({patient_user.first_name} {patient_user.last_name})")
    print(f"Doctor User: {doctor_user.username}")
    print(f"Notifications Created: {len(created_notifications)}")
    print(f"Messages Created: {len(created_messages)}")
    
    # Count unread items
    unread_notifications = Notification.objects.filter(user=patient_user, is_read=False).count()
    unread_messages = Message.objects.filter(recipient=patient_user, is_read=False).count()
    
    print(f"Unread Notifications: {unread_notifications}")
    print(f"Unread Messages: {unread_messages}")
    print("\nTest data created successfully!")
    print(f"You can now login with username: {patient_user.username}, password: password123")

if __name__ == '__main__':
    create_test_data()
