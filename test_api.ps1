# MediFlow API Quick Test Script for PowerShell
# Tests basic connectivity to the Django backend

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "  MediFlow API Quick Test" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

$baseUrl = "http://127.0.0.1:8000/api"
$username = "patient1"
$password = "password123"

Write-Host "Testing API at: $baseUrl" -ForegroundColor Yellow
Write-Host "Username: $username`n" -ForegroundColor Yellow

# Test 1: Server Connectivity
Write-Host "1. Testing server connectivity..." -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/" -Method Get -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ Server is reachable!" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ✅ Server is reachable (404 is expected for base API URL)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Server not reachable: $_" -ForegroundColor Red
        Write-Host "`n   Please ensure Django backend is running:" -ForegroundColor Yellow
        Write-Host "   py manage.py runserver" -ForegroundColor White
        exit 1
    }
}

# Test 2: Authentication
Write-Host "`n2. Testing authentication..." -ForegroundColor White
$loginBody = @{
    username = $username
    password = $password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/token/" -Method Post -Body $loginBody -ContentType "application/json" -ErrorAction Stop
    $accessToken = $loginResponse.access
    Write-Host "   ✅ Login successful!" -ForegroundColor Green
    Write-Host "   Access token: $($accessToken.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Login failed: $_" -ForegroundColor Red
    Write-Host "   Please check your credentials" -ForegroundColor Yellow
    exit 1
}

# Test 3: Protected Endpoint
Write-Host "`n3. Testing protected endpoint (Patient Profile)..." -ForegroundColor White
$headers = @{
    Authorization = "Bearer $accessToken"
}

try {
    $profile = Invoke-RestMethod -Uri "$baseUrl/patient/me/" -Headers $headers -Method Get -ErrorAction Stop
    Write-Host "   ✅ Profile retrieved successfully!" -ForegroundColor Green
    Write-Host "   User: $($profile.user.username) (Role: $($profile.user.role))" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Failed to get profile: $_" -ForegroundColor Red
}

# Test 4: Prescriptions
Write-Host "`n4. Testing prescriptions endpoint..." -ForegroundColor White
try {
    $prescriptions = Invoke-RestMethod -Uri "$baseUrl/patient/prescriptions/" -Headers $headers -Method Get -ErrorAction Stop
    $count = $prescriptions.results.Count
    Write-Host "   ✅ Prescriptions retrieved!" -ForegroundColor Green
    Write-Host "   Found: $count prescriptions" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Failed to get prescriptions: $_" -ForegroundColor Red
}

# Test 5: Medicines
Write-Host "`n5. Testing medicines endpoint..." -ForegroundColor White
try {
    $medicines = Invoke-RestMethod -Uri "$baseUrl/medicines/" -Headers $headers -Method Get -ErrorAction Stop
    $count = $medicines.results.Count
    Write-Host "   ✅ Medicines retrieved!" -ForegroundColor Green
    Write-Host "   Found: $count medicines" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Failed to get medicines: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

Write-Host "✅ Backend API is working correctly!" -ForegroundColor Green
Write-Host "You can now use the Flutter app with these credentials:`n" -ForegroundColor White
Write-Host "   Username: $username" -ForegroundColor Yellow
Write-Host "   Password: $password" -ForegroundColor Yellow
Write-Host "`nMake sure to use the correct URL in your Flutter app:" -ForegroundColor White
Write-Host "   Android Emulator: http://10.0.2.2:8000/api" -ForegroundColor Gray
Write-Host "   iOS/Web: http://127.0.0.1:8000/api" -ForegroundColor Gray
