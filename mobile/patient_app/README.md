# Patient Mobile Application

This Flutter application provides patients with access to their medical information, prescriptions, and medicine catalog.

## Features Implemented

### 1. Authentication
- Patient login with username and password
- Secure token storage using Flutter Secure Storage
- Automatic token refresh for expired sessions
- Robust error handling for authentication failures
- Debug logging for token management

### 2. Patient Dashboard
- Welcome message with patient name and current date
- Prescription statistics (total, pending, dispensed) with visual cards
- Recent prescriptions list with improved styling
- Medical summary with key information
- Modern card-based design with shadows and rounded corners

### 3. Prescription Management
- View all prescriptions with status indicators
- Detailed prescription information with organized sections
- Prescription tracing for dispensed medications
- Enhanced UI with better visual hierarchy

### 4. Medical History
- Complete medical record viewing
- Blood type, allergies, chronic conditions
- Past surgeries, current medications
- Family and social history

### 5. Enhanced Medicine Catalog
- **Modern Grid Layout**: Card-based display with images
- **Advanced Search**: Search by name, generic name, or description
- **Category Filtering**: 9 predefined medicine categories
- **Price Information**: Price ranges for medicines
- **Availability Status**: Real-time stock indicators
- **Visual Design**: Color-coded category badges and professional UI

### 6. Medicine Detail View
- **Product Images**: High-quality medicine images with placeholders
- **Comprehensive Information**: Name, generic name, strength, form, description
- **Manufacturer Details**: Information about the medicine manufacturer
- **Price & Availability**: Price ranges and stock information across pharmacies
- **Batch Information**: Recent production batches with expiry dates
- **Pharmacy Map**: Interactive map showing nearby pharmacies with stock
- **Distance Calculation**: Shows how far each pharmacy is from the patient
- **Robust Error Handling**: Safe data access with proper null checking

### 7. Profile Management
- Personal information display
- Medical information summary
- Logout functionality

## Navigation

The app uses a bottom navigation bar with 5 tabs:
1. **Home** - Dashboard with overview information
2. **Prescriptions** - List of all prescriptions
3. **Medicines** - Medicine catalog with search and filters
4. **History** - Complete medical history
5. **Profile** - Personal and medical information

## API Integration

The app connects to a Django REST API with the following endpoints:
- `/api/token/` - Authentication
- `/api/patient/me/` - Patient profile
- `/api/patient/me/medical-record/` - Medical record
- `/api/patient/prescriptions/` - Prescription list
- `/api/prescriptions/{id}/` - Prescription detail
- `/api/medicines/` - Medicine list with search and filtering
- `/api/medicine/{id}/` - Medicine detail with batches
- `/api/medicine/{id}/availability/` - Medicine availability with location data

## Setup Instructions

1. Ensure the Django backend is running
2. Update the `baseUrl` in `lib/services/api_service.dart` if needed
3. Run `flutter pub get` to install dependencies
4. Run `flutter run` to start the application

## Dependencies

- `http` - For API requests
- `flutter_secure_storage` - For secure token storage
- `flutter_map` - For medicine availability maps
- `latlong2` - For map coordinates

## Enhanced Medicine Features

See [MEDICINE_FEATURES.md](MEDICINE_FEATURES.md) for detailed information about the enhanced medicine catalog and detail views.

## Mobile UI Improvements

See [MOBILE_UI_IMPROVEMENTS.md](MOBILE_UI_IMPROVEMENTS.md) for detailed information about the mobile UI enhancements.

## Authentication Fixes

See [AUTHENTICATION_FIXES.md](AUTHENTICATION_FIXES.md) for detailed information about the authentication improvements and fixes.

## Medicine Detail Fixes

See [MEDICINE_DETAIL_FIXES.md](MEDICINE_DETAIL_FIXES.md) for detailed information about the medicine detail screen improvements and fixes.