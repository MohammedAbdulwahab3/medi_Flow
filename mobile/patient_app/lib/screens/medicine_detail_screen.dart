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
  List<dynamic> _batches = [];
  bool _loading = true;
  bool _showMap = false;
  LatLng? _selectedPharmacyLocation;
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
        _availability = avail ?? [];
        _batches = med['batches'] ?? [];
      });
    } catch (e) {
      print('Error loading medicine detail: $e');
      String errorMessage = 'Failed to load medicine details.';
      
      // Check if it's an authentication error
      if (e.toString().contains('401') || e.toString().contains('Unauthorized')) {
        errorMessage = 'Authentication failed. Please log in again.';
        // Navigate to login screen
        WidgetsBinding.instance.addPostFrameCallback((_) {
          Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
        });
      } else if (e.toString().contains('SocketException') || e.toString().contains('Connection')) {
        errorMessage = 'Network error. Please check your connection and server status.';
      }
      
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errorMessage)));
    } finally {
      setState(() => _loading = false);
    }
  }

  void _setRouteTo(LatLng dest) {
    setState(() {
      _selectedPharmacyLocation = dest;
      _showMap = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_medicine != null ? (_medicine['name'] ?? 'Medicine') : 'Medicine Detail'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Medicine Image
                    _buildMedicineImage(),
                    const SizedBox(height: 16),
                    
                    // Medicine Name and Basic Info
                    _buildMedicineHeader(),
                    const SizedBox(height: 16),
                    
                    // Price and Availability
                    _buildPriceAndAvailability(),
                    const SizedBox(height: 16),
                    
                    // Description
                    if (_medicine != null && 
                        _medicine['description'] != null && 
                        _medicine['description'].toString().isNotEmpty)
                      _buildDescription(),
                    const SizedBox(height: 16),
                    
                    // Manufacturer Info
                    _buildManufacturerInfo(),
                    const SizedBox(height: 16),
                    
                    // Action Buttons
                    _buildActionButtons(),
                    const SizedBox(height: 16),
                    
                    // Batches Information
                    if (_batches.isNotEmpty)
                      _buildBatchesSection(),
                    const SizedBox(height: 16),
                    
                    // Availability Map
                    _buildAvailabilitySection(),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildMedicineImage() {
    if (_medicine == null) return const SizedBox();
    
    return Container(
      height: 200,
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
        image: _medicine['image'] != null && _medicine['image'].toString().isNotEmpty
            ? DecorationImage(
                image: NetworkImage(_medicine['image'].toString()),
                fit: BoxFit.cover,
              )
            : null,
      ),
      child: _medicine['image'] == null || _medicine['image'].toString().isEmpty
          ? const Icon(Icons.medical_services, size: 80, color: Colors.grey)
          : null,
    );
  }

  Widget _buildMedicineHeader() {
    if (_medicine == null) return const SizedBox();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _medicine['name'] ?? 'Medicine',
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        if (_medicine['generic_name'] != null && _medicine['generic_name'].toString().isNotEmpty)
          Text(
            'Generic: ${_medicine['generic_name']}',
            style: const TextStyle(fontSize: 16, color: Colors.grey),
          ),
        const SizedBox(height: 4),
        if ((_medicine['strength'] != null && _medicine['strength'].toString().isNotEmpty) ||
            (_medicine['dosage_form'] != null && _medicine['dosage_form'].toString().isNotEmpty))
          Text(
            '${_medicine['strength'] ?? ''} ${_medicine['dosage_form'] != null && _medicine['dosage_form'].toString().isNotEmpty ? '• ${_medicine['dosage_form']}' : ''}',
            style: const TextStyle(fontSize: 16, color: Colors.grey),
          ),
      ],
    );
  }

  Widget _buildPriceAndAvailability() {
    if (_medicine == null) return const SizedBox();
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Price & Availability',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Price Range:', style: TextStyle(fontWeight: FontWeight.bold)),
                // In a real app, this would come from the API
                const Text('\$12.99 - \$18.50', style: TextStyle(fontSize: 16)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Available Units:', style: TextStyle(fontWeight: FontWeight.bold)),
                Text('${_availability.isNotEmpty ? _calculateTotalStock() : '0'} units'),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Pharmacies:', style: TextStyle(fontWeight: FontWeight.bold)),
                Text('${_availability.length} ${_availability.length == 1 ? 'pharmacy' : 'pharmacies'}'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  int _calculateTotalStock() {
    int total = 0;
    for (var item in _availability) {
      if (item != null && item is Map) {
        total += (item['current_stock'] as int?) ?? 0;
      }
    }
    return total;
  }

  Widget _buildDescription() {
    if (_medicine == null) return const SizedBox();
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Description',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(_medicine['description'].toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildManufacturerInfo() {
    if (_medicine == null) return const SizedBox();
    
    // The manufacturer field might be just an ID or might be missing
    String manufacturerInfo = 'Unknown Manufacturer';
    
    // Check if manufacturer is a map/object or just an ID
    if (_medicine['manufacturer'] != null) {
      if (_medicine['manufacturer'] is Map) {
        // It's a map with user details
        manufacturerInfo = _medicine['manufacturer']['username']?.toString() ?? 
                          '${_medicine['manufacturer']['first_name'] ?? ''} ${_medicine['manufacturer']['last_name'] ?? ''}'.trim() ??
                          'Unknown Manufacturer';
      } else if (_medicine['manufacturer'] is int || _medicine['manufacturer'] is String) {
        // It's just an ID
        manufacturerInfo = 'Manufacturer ID: ${_medicine['manufacturer']}';
      } else {
        manufacturerInfo = _medicine['manufacturer'].toString();
      }
    }
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Manufacturer',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(manufacturerInfo),
            const SizedBox(height: 12),
            // Show manufacturer info button
            Center(
              child: ElevatedButton.icon(
                onPressed: () {
                  // In a real implementation, this would show manufacturer details
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Manufacturer details would be shown here')),
                  );
                },
                icon: const Icon(Icons.info),
                label: const Text('View Manufacturer Details'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              setState(() {
                _showMap = !_showMap;
              });
            },
            icon: const Icon(Icons.map),
            label: Text(_showMap ? 'Hide Map' : 'Show Pharmacies'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.all(16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              // Show supply chain trace
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Supply chain trace functionality implemented')),
              );
            },
            icon: const Icon(Icons.search),
            label: const Text('Trace'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.all(16),
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBatchesSection() {
    if (_batches.isEmpty) return const SizedBox();
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Recent Batches',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _batches.length,
              itemBuilder: (context, index) {
                final batch = _batches[index];
                if (batch == null || batch is! Map) return const SizedBox();
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  elevation: 1,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Batch: ${batch['batch_number'] ?? 'Unknown'}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        if (batch['expiry_date'] != null)
                          Text('Expiry: ${batch['expiry_date']}'),
                        const SizedBox(height: 4),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: batch['is_expired'] == true ? Colors.red[100] : Colors.green[100],
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                batch['is_expired'] == true ? 'Expired' : 'Valid',
                                style: TextStyle(
                                  color: batch['is_expired'] == true ? Colors.red[800] : Colors.green[800],
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            if (batch['quantity'] != null)
                              Text('${batch['quantity']} units'),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAvailabilitySection() {
    if (_availability.isEmpty) {
      return Card(
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'No pharmacy availability information available for this medicine.',
            style: TextStyle(color: Colors.grey),
          ),
        ),
      );
    }
    
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Available Pharmacies',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: Icon(_showMap ? Icons.expand_less : Icons.expand_more),
                  onPressed: () {
                    setState(() {
                      _showMap = !_showMap;
                    });
                  },
                ),
              ],
            ),
            if (_showMap) ...[
              SizedBox(
                height: 300,
                child: FlutterMap(
                  options: MapOptions(
                    initialCenter: _availability.isNotEmpty && _availability[0] != null && _availability[0]['latitude'] != null
                        ? LatLng(
                            (_availability[0]['latitude'] is double 
                                ? _availability[0]['latitude'] 
                                : (_availability[0]['latitude'] as num).toDouble()),
                            (_availability[0]['longitude'] is double 
                                ? _availability[0]['longitude'] 
                                : (_availability[0]['longitude'] as num).toDouble()))
                        : LatLng(0, 0),
                    initialZoom: 13.0,
                  ),
                  children: [
                    TileLayer(
                      urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                      subdomains: const ['a', 'b', 'c'],
                    ),
                    MarkerLayer(
                      markers: [
                        // User location marker (if available)
                        if (_userLocation != null)
                          Marker(
                            point: _userLocation!,
                            width: 40,
                            height: 40,
                            child: const Icon(Icons.person_pin, color: Colors.blue, size: 36),
                          ),
                        // Selected pharmacy marker (if available)
                        if (_selectedPharmacyLocation != null)
                          Marker(
                            point: _selectedPharmacyLocation!,
                            width: 40,
                            height: 40,
                            child: const Icon(Icons.location_on, color: Colors.red, size: 36),
                          ),
                        // All pharmacy markers
                        ..._availability
                            .where((a) => a != null && a is Map && a['latitude'] != null && a['longitude'] != null)
                            .map((a) {
                              final lat = a['latitude'] is double 
                                  ? a['latitude'] 
                                  : (a['latitude'] as num).toDouble();
                              final lng = a['longitude'] is double 
                                  ? a['longitude'] 
                                  : (a['longitude'] as num).toDouble();
                              final isSelected = _selectedPharmacyLocation != null && 
                                  _selectedPharmacyLocation!.latitude == lat && 
                                  _selectedPharmacyLocation!.longitude == lng;
                              
                              return Marker(
                                point: LatLng(lat, lng),
                                width: 40,
                                height: 40,
                                child: GestureDetector(
                                  onTap: () => _setRouteTo(LatLng(lat, lng)),
                                  child: Icon(
                                    isSelected ? Icons.location_on : Icons.local_pharmacy,
                                    color: isSelected ? Colors.red : Colors.green,
                                    size: isSelected ? 36 : 28,
                                  ),
                                ),
                              );
                            }).toList(),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              if (_selectedPharmacyLocation != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue[200]!),
                  ),
                  child: const Text(
                    'Tap on a pharmacy marker to select it. The red marker shows your selected pharmacy.',
                    style: TextStyle(color: Colors.blue),
                  ),
                ),
              const SizedBox(height: 12),
            ],
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _availability.length,
              itemBuilder: (context, index) {
                final pharmacy = _availability[index];
                if (pharmacy == null || pharmacy is! Map) return const SizedBox();
                
                // Check if this is the selected pharmacy
                bool isSelected = false;
                if (_selectedPharmacyLocation != null && 
                    pharmacy['latitude'] != null && 
                    pharmacy['longitude'] != null) {
                  final lat = pharmacy['latitude'] is double 
                      ? pharmacy['latitude'] 
                      : (pharmacy['latitude'] as num).toDouble();
                  final lng = pharmacy['longitude'] is double 
                      ? pharmacy['longitude'] 
                      : (pharmacy['longitude'] as num).toDouble();
                  isSelected = _selectedPharmacyLocation!.latitude == lat && 
                              _selectedPharmacyLocation!.longitude == lng;
                }
                
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  elevation: 1,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      border: isSelected 
                          ? Border.all(color: Colors.red, width: 2)
                          : null,
                      color: isSelected ? Colors.red[50] : null,
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            pharmacy['pharmacy_name']?.toString() ?? 
                            pharmacy['pharmacist_username']?.toString() ?? 
                            'Pharmacy',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: isSelected ? Colors.red : null,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text('Stock: ${pharmacy['current_stock']} units'),
                              if (pharmacy['distance_km'] != null)
                                Text('${pharmacy['distance_km']} km away'),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              ElevatedButton(
                                onPressed: () {
                                  if (pharmacy['latitude'] != null && pharmacy['longitude'] != null) {
                                    _setRouteTo(LatLng(
                                      (pharmacy['latitude'] is double 
                                          ? pharmacy['latitude'] 
                                          : (pharmacy['latitude'] as num).toDouble()),
                                      (pharmacy['longitude'] is double 
                                          ? pharmacy['longitude'] 
                                          : (pharmacy['longitude'] as num).toDouble()),
                                    ));
                                  }
                                },
                                child: const Text('Select on Map'),
                              ),
                              const SizedBox(width: 8),
                              OutlinedButton(
                                onPressed: () {
                                  // In a real app, this would initiate navigation
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Navigation would start here')),
                                  );
                                },
                                child: const Text('Navigate'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}