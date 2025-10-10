#!/usr/bin/env python
"""
Backend API Endpoint Tester for MediFlow
Tests all API endpoints to verify backend functionality
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
TEST_USERNAME = "patient1"  # Update with actual test username
TEST_PASSWORD = "password123"  # Update with actual test password

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
        
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Optional[Dict] = None, use_auth: bool = True) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if use_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                print(f"❌ Unsupported method: {method}")
                return False
                
            status = "✅ PASS" if response.status_code in [200, 201, 204] else "❌ FAIL"
            print(f"{status} [{response.status_code}] {name}: {method} {endpoint}")
            
            if response.status_code not in [200, 201, 204]:
                try:
                    error_detail = response.json()
                    print(f"     Error: {error_detail}")
                except:
                    print(f"     Error: {response.text[:100]}")
                    
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": response.status_code in [200, 201, 204]
            })
            
            return response.status_code in [200, 201, 204], response
            
        except requests.exceptions.ConnectionError:
            print(f"❌ FAIL {name}: Connection error - Is the server running?")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "success": False,
                "error": "Connection error"
            })
            return False, None
        except Exception as e:
            print(f"❌ FAIL {name}: {str(e)}")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "success": False,
                "error": str(e)
            })
            return False, None
            
    def run_tests(self):
        """Run all API endpoint tests"""
        print("\n" + "🔍 MediFlow Backend API Test Suite 🔍".center(60))
        print(f"Base URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Server Health
        self.print_header("1. SERVER CONNECTIVITY")
        success, _ = self.test_endpoint("Server Health", "GET", "/", use_auth=False)
        
        if not success:
            print("\n⚠️  Server not reachable. Please ensure:")
            print("   1. Django backend is running: py manage.py runserver")
            print("   2. URL is correct: http://127.0.0.1:8000")
            return
            
        # Test 2: Authentication
        self.print_header("2. AUTHENTICATION")
        
        # Login
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        success, response = self.test_endpoint("Login", "POST", "/token/", 
                                              data=login_data, use_auth=False)
        
        if success and response:
            data = response.json()
            self.access_token = data.get("access")
            self.refresh_token = data.get("refresh")
            print(f"     Access Token: {self.access_token[:20]}..." if self.access_token else "     No access token")
            
            # Token Refresh
            if self.refresh_token:
                refresh_data = {"refresh": self.refresh_token}
                success, response = self.test_endpoint("Token Refresh", "POST", "/token/refresh/",
                                                      data=refresh_data, use_auth=False)
                if success and response:
                    new_access = response.json().get("access")
                    if new_access:
                        self.access_token = new_access
                        print(f"     New Access Token: {new_access[:20]}...")
        else:
            print("\n⚠️  Authentication failed. Cannot continue with authenticated endpoints.")
            print(f"   Please check credentials: username='{TEST_USERNAME}'")
            return
            
        # Test 3: Patient Endpoints
        self.print_header("3. PATIENT ENDPOINTS")
        
        self.test_endpoint("Patient Profile", "GET", "/patient/me/")
        self.test_endpoint("Medical Record", "GET", "/patient/me/medical-record/")
        self.test_endpoint("Assigned Doctors", "GET", "/patient/assigned-doctors/")
        
        # Test 4: Prescription Endpoints
        self.print_header("4. PRESCRIPTION ENDPOINTS")
        
        success, response = self.test_endpoint("Prescriptions List", "GET", "/patient/prescriptions/")
        
        if success and response:
            data = response.json()
            prescriptions = data.get("results", [])
            if prescriptions:
                first_id = prescriptions[0].get("id")
                if first_id:
                    self.test_endpoint("Prescription Detail", "GET", f"/prescriptions/{first_id}/")
                    
        # Test 5: Medicine Endpoints
        self.print_header("5. MEDICINE ENDPOINTS")
        
        success, response = self.test_endpoint("Medicines List", "GET", "/medicines/")
        
        if success and response:
            data = response.json()
            medicines = data.get("results", [])
            if medicines:
                first_id = medicines[0].get("id")
                if first_id:
                    self.test_endpoint("Medicine Detail", "GET", f"/medicine/{first_id}/")
                    self.test_endpoint("Medicine Availability", "GET", f"/medicine/{first_id}/availability/")
                    
        # Test 6: Analytics & Search
        self.print_header("6. ANALYTICS & SEARCH")
        
        self.test_endpoint("Role-based Analytics", "GET", "/analytics/")
        
        search_data = {
            "query": "test",
            "type": "all",
            "category": "all"
        }
        self.test_endpoint("Advanced Search", "POST", "/search/", data=search_data)
        
        # Test 7: Optional/Fallback Endpoints
        self.print_header("7. OPTIONAL ENDPOINTS (May Not Exist)")
        
        # These might not exist, so we expect them to potentially fail
        self.test_endpoint("Notifications", "GET", "/notifications/")
        self.test_endpoint("Messages", "GET", "/messages/")
        self.test_endpoint("Profile Update", "PUT", "/patient/me/", 
                          data={"phone": "+1234567890"})
        
        # Print Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        self.print_header("TEST SUMMARY")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "N/A")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['method']} {result['endpoint']}")
                    
        # Recommendations
        print("\n" + "="*60)
        print(" RECOMMENDATIONS")
        print("="*60)
        
        if failed == 0:
            print("✅ All tests passed! Backend is fully functional.")
        elif passed > total * 0.7:
            print("⚠️  Most tests passed. Some optional endpoints may not be implemented.")
            print("   This is expected behavior. The Flutter app has fallbacks.")
        else:
            print("❌ Many tests failed. Please check:")
            print("   1. Database migrations: py manage.py migrate")
            print("   2. Test data exists: py manage.py createsuperuser")
            print("   3. All apps are installed in settings.py")
            print("   4. URLs are properly configured")
            
def main():
    """Main function"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         MediFlow Backend API Endpoint Tester             ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    # You can modify these for testing
    print("\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Username: {TEST_USERNAME}")
    print(f"  Password: {'*' * len(TEST_PASSWORD)}")
    
    response = input("\nProceed with testing? (y/n): ")
    if response.lower() != 'y':
        print("Testing cancelled.")
        return
        
    tester = APITester()
    tester.run_tests()
    
    # Save results to file
    save_results = input("\nSave results to file? (y/n): ")
    if save_results.lower() == 'y':
        filename = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "base_url": BASE_URL,
                "results": tester.test_results
            }, f, indent=2)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
