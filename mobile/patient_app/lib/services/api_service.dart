import 'dart:convert';
import 'dart:math' as math show min;
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {

  // Default baseUrl: use 127.0.0.1 for web/iOS simulator, 10.0.2.2 for Android emulator.
  // You can call ApiService.setBaseUrl('http://<host>:8000/api') at app startup to override.
  static String baseUrl = kIsWeb ? 'http://127.0.0.1:8000/api' : 'http://10.0.2.2:8000/api';
  static final _storage = FlutterSecureStorage();
  // simple in-memory fallback for web (flutter_secure_storage may not work on web)
  static final Map<String, String> _webStorage = {};

  static Future<void> _write(String key, String? value) async {
    try {
      if (kIsWeb) {
        if (value == null) {
          _webStorage.remove(key);
        } else {
          _webStorage[key] = value;
        }
        print('Web storage write: $key = ${value?.substring(0, math.min(20, value?.length ?? 0))}...');
      } else {
        if (value == null) {
          await _storage.delete(key: key);
          print('Secure storage delete: $key');
        } else {
          await _storage.write(key: key, value: value);
          print('Secure storage write: $key = ${value.substring(0, math.min(20, value.length))}...');
        }
      }
    } catch (e) {
      print('Storage write error for key $key: $e');
    }
  }

  static Future<String?> _read(String key) async {
    try {
      if (kIsWeb) {
        final value = _webStorage[key];
        print('Web storage read: $key = ${value?.substring(0, math.min(20, value?.length ?? 0))}...');
        return value;
      } else {
        final value = await _storage.read(key: key);
        print('Secure storage read: $key = ${value?.substring(0, math.min(20, value?.length ?? 0))}...');
        return value;
      }
    } catch (e) {
      print('Storage read error for key $key: $e');
      return null;
    }
  }

  static Future<bool> login(String username, String password) async {
    final url = Uri.parse('$baseUrl/token/');
    try {
      final body = json.encode({'username': username, 'password': password});
      print('Login POST -> $url body: $body');
      final res = await http.post(url, headers: {'Content-Type': 'application/json'}, body: body);
      print('Login response status: ${res.statusCode}');
      print('Login response body: ${res.body}');
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        final accessToken = data['access'];
        final refreshToken = data['refresh'];
        print('Access token length: ${accessToken?.length ?? 0}');
        print('Refresh token length: ${refreshToken?.length ?? 0}');
        await _write('access', accessToken);
        await _write('refresh', refreshToken);
        print('Login successful. Access token stored: ${accessToken != null && accessToken.isNotEmpty}');
        return true;
      } else {
        // helpful debug: include response body for UI feedback
        print('Login failed: ${res.statusCode} - ${res.body}');
        // store last error message for UI
        await _write('last_login_error', res.body);
        return false;
      }
    } catch (e) {
      print('Login exception: $e');
      await _write('last_login_error', e.toString());
      return false;
    }
  }

  static Future<Map<String, String>> _authHeaders() async {
    final token = await _read('access');
    print('Retrieved token: $token');
    print('Token length: ${token?.length ?? 0}');
    // Ensure proper Bearer token format
    final headers = {
      'Content-Type': 'application/json',
      'Authorization': token != null && token.isNotEmpty ? 'Bearer $token' : ''
    };
    print('Auth headers: $headers');
    return headers;
  }

  static Future<bool> _refreshToken() async {
    final refreshToken = await _read('refresh');
    if (refreshToken == null || refreshToken.isEmpty) {
      print('No refresh token available');
      return false;
    }

    final url = Uri.parse('$baseUrl/token/refresh/');
    try {
      final body = json.encode({'refresh': refreshToken});
      print('Refreshing token with refresh token: ${refreshToken.substring(0, math.min(10, refreshToken.length))}...');
      
      final res = await http.post(url, 
        headers: {'Content-Type': 'application/json'}, 
        body: body
      );
      
      print('Token refresh response status: ${res.statusCode}');
      print('Token refresh response body: ${res.body}');
      
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        final newAccessToken = data['access'];
        if (newAccessToken != null && newAccessToken.isNotEmpty) {
          await _write('access', newAccessToken);
          print('Token refreshed successfully');
          return true;
        } else {
          print('Token refresh failed: No access token in response');
          return false;
        }
      } else {
        print('Token refresh failed: ${res.statusCode} - ${res.body}');
        // If refresh token is invalid, clear all tokens
        if (res.statusCode == 401) {
          await _write('access', null);
          await _write('refresh', null);
          print('Cleared invalid tokens due to 401 on refresh');
        }
        return false;
      }
    } catch (e) {
      print('Token refresh exception: $e');
      return false;
    }
  }

  static Future<http.Response> _makeAuthenticatedRequest(
    Uri url, {
    Map<String, String>? additionalHeaders,
    String method = 'GET',
    Object? body,
  }) async {
    var headers = await _authHeaders();
    
    // Only add additional headers if they are not null
    if (additionalHeaders != null && additionalHeaders.isNotEmpty) {
      headers.addAll(additionalHeaders);
    }

    print('Making $method request to: $url');
    print('Request headers: $headers');

    http.Response res;
    try {
      switch (method) {
        case 'POST':
          res = await http.post(url, headers: headers, body: body);
          break;
        case 'PUT':
          res = await http.put(url, headers: headers, body: body);
          break;
        case 'DELETE':
          res = await http.delete(url, headers: headers);
          break;
        default:
          res = await http.get(url, headers: headers);
      }
    } on SocketException catch (e) {
      // Network-level error (host unreachable, no connection)
      print('Network error when making request to $url: $e');
      rethrow;
    } catch (e) {
      print('Unexpected error when making request to $url: $e');
      rethrow;
    }

    print('Response status: ${res.statusCode}');
    print('Response headers: ${res.headers}');
    if (res.body.length < 1000) {  // Only print body if it's not too large
      print('Response body: ${res.body}');
    }

    // If unauthorized, try to refresh token and retry
    if (res.statusCode == 401) {
      print('Received 401, attempting to refresh token');
      final refreshed = await _refreshToken();
      if (refreshed) {
        print('Token refresh successful, retrying request');
        // Retry the request with new token
        headers = await _authHeaders();
        // Add additional headers again if they exist
        if (additionalHeaders != null && additionalHeaders.isNotEmpty) {
          headers.addAll(additionalHeaders);
        }
        
        print('Retrying $method request to: $url');
        print('Retry headers: $headers');
        
        switch (method) {
          case 'POST':
            res = await http.post(url, headers: headers, body: body);
            break;
          case 'PUT':
            res = await http.put(url, headers: headers, body: body);
            break;
          case 'DELETE':
            res = await http.delete(url, headers: headers);
            break;
          default:
            res = await http.get(url, headers: headers);
        }
        
        print('Retry response status: ${res.statusCode}');
        if (res.body.length < 1000) {  // Only print body if it's not too large
          print('Retry response body: ${res.body}');
        }
      } else {
        print('Token refresh failed, returning 401 response');
      }
    }

    return res;
  }

  /// Override the base API URL at runtime (helpful for testing on physical devices)
  static void setBaseUrl(String url) {
    // ensure no trailing slash and ensure '/api' suffix if not present
    var u = url.trim();
    if (u.endsWith('/')) u = u.substring(0, u.length - 1);
    if (!u.endsWith('/api')) {
      // allow passing host like http://192.168.1.10:8000 -> normalize to /api
      if (u.endsWith('/api')) {
        // noop
      } else {
        u = '$u/api';
      }
    }
    baseUrl = u;
    print('ApiService baseUrl set to: $baseUrl');
  }

  /// Quick server health check / connectivity diagnostic. Returns a map with status and message.
  /// Use this from app startup or a debug screen to confirm the server is reachable.
  static Future<Map<String, dynamic>> checkServer({Duration timeout = const Duration(seconds: 5)}) async {
    final url = Uri.parse('$baseUrl/');
    try {
      final res = await http.get(url).timeout(timeout);
      return {
        'ok': res.statusCode >= 200 && res.statusCode < 500,
        'statusCode': res.statusCode,
        'body': res.body,
      };
    } on SocketException catch (e) {
      return {'ok': false, 'error': 'Network error: $e'};
    } on Exception catch (e) {
      return {'ok': false, 'error': 'Exception: $e'};
    }
  }

  static Future<dynamic> getPatientProfile() async {
    final url = Uri.parse('$baseUrl/patient/me/');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get patient profile failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load patient profile: ${res.statusCode}');
  }

  static Future<dynamic> getMedicalRecord() async {
    final url = Uri.parse('$baseUrl/patient/me/medical-record/');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get medical record failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load medical record: ${res.statusCode}');
  }

  static Future<dynamic> getPrescriptions() async {
    final url = Uri.parse('$baseUrl/patient/prescriptions/');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get prescriptions failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load prescriptions: ${res.statusCode}');
  }

  static Future<dynamic> getPrescriptionDetail(int id) async {
    final url = Uri.parse('$baseUrl/prescriptions/$id/');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    throw Exception('Failed to load prescription');
  }
  
  static Future<String?> getLastLoginError() async {
    return await _read('last_login_error');
  }

  static Future<dynamic> getMedicines({String? search, String? category, int page = 1}) async {
    final q = <String>[];
    if (search != null && search.isNotEmpty) q.add('search=${Uri.encodeComponent(search)}');
    if (category != null && category.isNotEmpty) q.add('category=$category');
    q.add('page=$page');
    final url = Uri.parse('$baseUrl/medicines/?${q.join('&')}');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get medicines failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load medicines');
  }

  static Future<dynamic> getMedicineAvailability(int id, {double? lat, double? lng, double? radiusKm}) async {
    final q = <String>[];
    if (lat != null && lng != null) {
      q.add('lat=$lat');
      q.add('lng=$lng');
    }
    if (radiusKm != null) q.add('radius_km=$radiusKm');
    final url = Uri.parse('$baseUrl/medicine/$id/availability/${q.isNotEmpty ? '?${q.join('&')}' : ''}');
    print('Making GET request to: $url');
    
    // Medicine availability might not require authentication
    final res = await http.get(url, headers: {'Content-Type': 'application/json'});
    print('Availability response status: ${res.statusCode}');
    print('Availability response body: ${res.body}');
    
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get availability failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load availability');
  }

  static Future<dynamic> getMedicineDetail(int id) async {
    final url = Uri.parse('$baseUrl/medicine/$id/');
    print('Making GET request to: $url');
    final res = await _makeAuthenticatedRequest(url);
    print('Response status: ${res.statusCode}');
    print('Response body: ${res.body}');
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get medicine detail failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load medicine detail');
  }
  
  static Future<dynamic> getMedicineCatalog({String? search, String? category}) async {
    // This would be a new endpoint that provides enhanced medicine data
    // For now, we'll use the existing medicines endpoint but with additional processing
    return await getMedicines(search: search, category: category);
  }
  
  static Future<void> clearTokens() async {
    await _write('access', null);
    await _write('refresh', null);
    print('All tokens cleared');
  }
  
  // Debug function to check if token is stored
  static Future<void> debugToken() async {
    final token = await _read('access');
    print('DEBUG: Current access token: $token');
    print('DEBUG: Access token length: ${token?.length ?? 0}');
    final refreshToken = await _read('refresh');
    print('DEBUG: Current refresh token: $refreshToken');
    print('DEBUG: Refresh token length: ${refreshToken?.length ?? 0}');
  }
}