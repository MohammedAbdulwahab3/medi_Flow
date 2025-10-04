import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {

  static String baseUrl = kIsWeb ? 'http://127.0.0.1:8000/api' : 'http://10.0.2.2:8000/api';
  static final _storage = FlutterSecureStorage();
  // simple in-memory fallback for web (flutter_secure_storage may not work on web)
  static final Map<String, String> _webStorage = {};

  static Future<void> _write(String key, String? value) async {
    if (kIsWeb) {
      if (value == null) {
        _webStorage.remove(key);
      } else {
        _webStorage[key] = value;
      }
    } else {
      if (value == null) return await _storage.delete(key: key);
      await _storage.write(key: key, value: value);
    }
  }

  static Future<String?> _read(String key) async {
    if (kIsWeb) return _webStorage[key];
    return await _storage.read(key: key);
  }

  static Future<bool> login(String username, String password) async {
    final url = Uri.parse('$baseUrl/token/');
    try {
      final body = json.encode({'username': username, 'password': password});
      print('Login POST -> $url body: $body');
      final res = await http.post(url, headers: {'Content-Type': 'application/json'}, body: body);
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        await _write('access', data['access']);
        await _write('refresh', data['refresh']);
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
  return {'Content-Type': 'application/json', 'Authorization': 'Bearer ${token ?? ''}'};
  }

  static Future<dynamic> getPrescriptions() async {
  final url = Uri.parse('$baseUrl/patient/prescriptions/');
    final headers = await _authHeaders();
    final res = await http.get(url, headers: headers);
  if (res.statusCode == 200) return json.decode(res.body);
  print('Get prescriptions failed: ${res.statusCode} - ${res.body}');
  throw Exception('Failed to load prescriptions: ${res.statusCode}');
  }

  static Future<dynamic> getPrescriptionDetail(int id) async {
    final url = Uri.parse('$baseUrl/prescriptions/$id/');
    final headers = await _authHeaders();
    final res = await http.get(url, headers: headers);
    if (res.statusCode == 200) return json.decode(res.body);
    throw Exception('Failed to load prescription');
  }
  static Future<String?> getLastLoginError() async {
    return await _read('last_login_error');
  }

  static Future<dynamic> getMedicines({String? search, int page = 1}) async {
    final q = <String>[];
    if (search != null && search.isNotEmpty) q.add('search=${Uri.encodeComponent(search)}');
    q.add('page=$page');
    final url = Uri.parse('$baseUrl/medicines/?${q.join('&')}');
    final headers = await _authHeaders();
    final res = await http.get(url, headers: headers);
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
    final headers = await _authHeaders();
    final res = await http.get(url, headers: headers);
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get availability failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load availability');
  }

  static Future<dynamic> getMedicineDetail(int id) async {
    final url = Uri.parse('$baseUrl/medicine/$id/');
    final headers = await _authHeaders();
    final res = await http.get(url, headers: headers);
    if (res.statusCode == 200) return json.decode(res.body);
    print('Get medicine detail failed: ${res.statusCode} - ${res.body}');
    throw Exception('Failed to load medicine detail');
  }
}
