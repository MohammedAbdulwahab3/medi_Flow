import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/api_service.dart';

class MedicineDetailScreen extends StatefulWidget {
  final int medicineId;
  const MedicineDetailScreen({super.key, required this.medicineId});

  @override
  State<MedicineDetailScreen> createState() => _MedicineDetailScreenState();
}

class _MedicineDetailScreenState extends State<MedicineDetailScreen> {
  dynamic _medicine;
  List<dynamic> _availability = [];
  bool _loading = true;

  LatLng? _userLocation;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
  final med = await ApiService.getMedicineDetail(widget.medicineId);
      final avail = await ApiService.getMedicineAvailability(widget.medicineId);
      setState(() {
        _medicine = med;
        _availability = avail;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load medicine')));
    } finally {
      setState(() => _loading = false);
    }
  }

  void _setRouteTo(LatLng dest) {
    setState(() {
      _userLocation = dest; // simple: route is a straight line from origin (0,0) or user location if known
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_medicine != null ? (_medicine['name'] ?? 'Medicine') : 'Medicine')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Expanded(
                  child: FlutterMap(
                    options: MapOptions(
                      initialCenter: _availability.isNotEmpty && _availability[0]['latitude'] != null
                          ? LatLng((_availability[0]['latitude'] as num).toDouble(), (_availability[0]['longitude'] as num).toDouble())
                          : LatLng(0, 0),
                      initialZoom: 13.0,
                    ),
                    children: [
                      TileLayer(
                        urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        subdomains: const ['a', 'b', 'c'],
                      ),
                      MarkerLayer(
                        markers: _availability.where((a) => a['latitude'] != null && a['longitude'] != null).map((a) {
                          final lat = a['latitude'] is double ? a['latitude'] : (a['latitude'] as num).toDouble();
                          final lng = a['longitude'] is double ? a['longitude'] : (a['longitude'] as num).toDouble();
                          return Marker(
                            point: LatLng(lat, lng),
                            width: 80,
                            height: 80,
                            child: GestureDetector(
                              onTap: () => _setRouteTo(LatLng(lat, lng)),
                              child: const Icon(Icons.location_on, color: Colors.red, size: 36),
                            ),
                          );
                        }).toList(),
                      ),
                      if (_userLocation != null) MarkerLayer(
                        markers: [Marker(point: _userLocation!, width: 10, height: 10, child: const Icon(Icons.flag, color: Colors.blue))],
                      ),
                    ],
                  ),
                ),
                SizedBox(
                  height: 160,
                  child: ListView.builder(
                    itemCount: _availability.length,
                    itemBuilder: (context, index) {
                      final a = _availability[index];
                      return ListTile(
                        title: Text(a['pharmacy_name'] ?? a['pharmacist_username'] ?? 'Pharmacy'),
                        subtitle: Text('Stock: ${a['current_stock']} • Distance: ${a['distance_km'] ?? '-'} km'),
                        trailing: ElevatedButton(onPressed: () {
                          if (a['latitude'] != null && a['longitude'] != null) {
                            _setRouteTo(LatLng((a['latitude'] as num).toDouble(), (a['longitude'] as num).toDouble()));
                          }
                        }, child: const Text('Route')),
                      );
                    },
                  ),
                ),
              ],
            ),
    );
  }
}
