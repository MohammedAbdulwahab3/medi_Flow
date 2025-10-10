#!/usr/bin/env python
"""
Test script to verify admin fix for NoReverseMatch error
Run this after applying the fix to verify everything works
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medi_flow.settings')
django.setup()

from django.contrib import admin
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

def test_admin_configuration():
    """Test that admin is properly configured"""
    print("=" * 60)
    print("ADMIN CONFIGURATION TEST")
    print("=" * 60)
    
    # Test 1: Check if User model is registered
    print("\n1. Checking if custom User model is registered...")
    if User in admin.site._registry:
        print("   ✅ Custom User model is registered in admin")
    else:
        print("   ❌ Custom User model is NOT registered in admin")
        return False
    
    # Test 2: Check AUTH_USER_MODEL setting
    print("\n2. Checking AUTH_USER_MODEL setting...")
    from django.conf import settings
    if settings.AUTH_USER_MODEL == 'authentication_app.User':
        print(f"   ✅ AUTH_USER_MODEL is correctly set to: {settings.AUTH_USER_MODEL}")
    else:
        print(f"   ❌ AUTH_USER_MODEL is incorrect: {settings.AUTH_USER_MODEL}")
        return False
    
    # Test 3: Check if URL patterns are resolvable
    print("\n3. Checking admin URL patterns...")
    try:
        url = reverse('admin:authentication_app_user_changelist')
        print(f"   ✅ User changelist URL resolved: {url}")
    except Exception as e:
        print(f"   ❌ Failed to resolve user changelist URL: {e}")
        return False
    
    try:
        url = reverse('admin:authentication_app_user_add')
        print(f"   ✅ User add URL resolved: {url}")
    except Exception as e:
        print(f"   ❌ Failed to resolve user add URL: {e}")
        return False
    
    # Test 4: Check registered models
    print("\n4. Checking all registered admin models...")
    registered_models = []
    for model, model_admin in admin.site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        registered_models.append(f"{app_label}.{model_name}")
    
    print(f"   ✅ Total registered models: {len(registered_models)}")
    print("\n   Registered models:")
    for model_name in sorted(registered_models):
        print(f"      - {model_name}")
    
    # Test 5: Check if old auth.User is NOT registered
    print("\n5. Checking that default auth.User is not registered...")
    try:
        from django.contrib.auth.models import User as DjangoUser
        if DjangoUser in admin.site._registry:
            print("   ⚠️  WARNING: Default Django User model is still registered!")
            print("      This might cause conflicts.")
        else:
            print("   ✅ Default Django User model is not registered (correct)")
    except ImportError:
        print("   ✅ Default Django User model doesn't exist (using custom model)")
    
    # Test 6: Check User model fields
    print("\n6. Checking custom User model fields...")
    expected_fields = ['role', 'license_number', 'national_id', 'phone', 'address']
    user_fields = [f.name for f in User._meta.get_fields()]
    
    missing_fields = [f for f in expected_fields if f not in user_fields]
    if missing_fields:
        print(f"   ⚠️  WARNING: Missing expected fields: {missing_fields}")
    else:
        print(f"   ✅ All expected custom fields are present")
    
    print(f"\n   Custom User model fields: {', '.join(expected_fields)}")
    
    # Test 7: Check UserAdmin configuration
    print("\n7. Checking UserAdmin configuration...")
    user_admin = admin.site._registry[User]
    if hasattr(user_admin, 'list_display'):
        print(f"   ✅ UserAdmin list_display: {user_admin.list_display}")
    if hasattr(user_admin, 'list_filter'):
        print(f"   ✅ UserAdmin list_filter: {user_admin.list_filter}")
    if hasattr(user_admin, 'search_fields'):
        print(f"   ✅ UserAdmin search_fields: {user_admin.search_fields}")
    
    return True


def test_user_count():
    """Test user count and display sample users"""
    print("\n" + "=" * 60)
    print("USER DATABASE TEST")
    print("=" * 60)
    
    total_users = User.objects.count()
    print(f"\nTotal users in database: {total_users}")
    
    if total_users > 0:
        print("\nSample users:")
        for user in User.objects.all()[:5]:
            print(f"   - {user.username} ({user.get_role_display()}) - Staff: {user.is_staff}, Superuser: {user.is_superuser}")
    else:
        print("\n⚠️  No users found in database.")
        print("   Create a superuser with: python manage.py createsuperuser")
    
    # Check for superusers
    superusers = User.objects.filter(is_superuser=True).count()
    if superusers > 0:
        print(f"\n✅ Found {superusers} superuser(s) - you can access admin")
    else:
        print("\n❌ No superusers found - create one to access admin:")
        print("   python manage.py createsuperuser")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MEDIFLOW ADMIN FIX VERIFICATION")
    print("=" * 60)
    
    try:
        # Run configuration tests
        config_ok = test_admin_configuration()
        
        # Run user tests
        test_user_count()
        
        # Final summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if config_ok:
            print("\n✅ All configuration tests passed!")
            print("\nNext steps:")
            print("1. Start the Django server: python manage.py runserver")
            print("2. Access admin at: http://127.0.0.1:8000/admin/")
            print("3. Login with your superuser credentials")
            print("4. Verify that the Users link works correctly")
        else:
            print("\n❌ Some tests failed. Please review the output above.")
            return 1
        
        print("\n" + "=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
