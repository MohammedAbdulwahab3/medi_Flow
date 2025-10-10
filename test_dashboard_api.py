#!/usr/bin/env python
"""
Quick API test script to verify dashboard endpoints are working
Run this to test the backend before testing the Flutter app
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'

def test_login():
    """Test login with patient1 credentials"""
    url = f'{BASE_URL}/token/'
    data = {
        'username': 'patient1',
        'password': 'password123'
    }
    
    print("[LOGIN] Testing login...")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        tokens = response.json()
        print("[SUCCESS] Login successful!")
        print(f"   Access token length: {len(tokens.get('access', ''))}")
        return tokens['access']
    else:
        print(f"[ERROR] Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_endpoints(access_token):
    """Test all dashboard-related endpoints"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    endpoints = [
        ('Patient Profile', '/patient/me/'),
        ('Prescriptions', '/patient/prescriptions/'),
        ('Assigned Doctors', '/patient/assigned-doctors/'),
        ('Notifications', '/patient/notifications/'),
        ('Messages', '/patient/messages/'),
        ('Unread Counts', '/patient/unread-counts/'),
        ('Analytics', '/analytics/'),
    ]
    
    results = {}
    
    for name, endpoint in endpoints:
        url = f'{BASE_URL}{endpoint}'
        print(f"\n[TEST] Testing {name}...")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[SUCCESS] {name} - Success!")
                
                # Show relevant data counts
                if 'results' in data:
                    print(f"   Items: {len(data['results'])}")
                elif isinstance(data, dict):
                    if 'analytics_data' in data:
                        analytics = data['analytics_data']
                        if 'prescriptions' in analytics:
                            pres = analytics['prescriptions']
                            print(f"   Prescriptions - Total: {pres.get('total', 0)}, Pending: {pres.get('pending', 0)}")
                        if 'notifications' in analytics:
                            notif = analytics['notifications']
                            print(f"   Notifications - Unread: {notif.get('unread', 0)}")
                    else:
                        # Show key fields
                        key_fields = ['notifications', 'messages', 'total', 'count']
                        for field in key_fields:
                            if field in data:
                                print(f"   {field}: {data[field]}")
                
                results[name] = {'status': 'success', 'data': data}
            else:
                print(f"[ERROR] {name} - Failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results[name] = {'status': 'failed', 'code': response.status_code}
                
        except Exception as e:
            print(f"[ERROR] {name} - Error: {str(e)}")
            results[name] = {'status': 'error', 'error': str(e)}
    
    return results

def main():
    print("MediFlow Dashboard API Test")
    print("=" * 50)
    
    # Test login
    access_token = test_login()
    if not access_token:
        print("\n[ERROR] Cannot proceed without valid access token")
        return
    
    # Test endpoints
    results = test_endpoints(access_token)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    
    print(f"[RESULT] Successful: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n[SUCCESS] All endpoints working! Dashboard should display real data.")
        print("\n[FLUTTER] You can now test the Flutter app with:")
        print("   1. Login with username: patient1, password: password123")
        print("   2. Check dashboard for real-time data")
        print("   3. Test refresh functionality")
        print("   4. Verify notifications and messages")
    else:
        print(f"\n[WARNING] {total_count - success_count} endpoints failed")
        print("   Dashboard may use fallback data for failed endpoints")
    
    print(f"\n[INFO] Backend running at: http://127.0.0.1:8000")
    print(f"[INFO] Admin panel: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    main()
