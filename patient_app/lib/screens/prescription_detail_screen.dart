import 'package:flutter/material.dart';
import '../services/api_service.dart';

class PrescriptionDetailScreen extends StatefulWidget {
  final int prescriptionId;
  const PrescriptionDetailScreen({super.key, required this.prescriptionId});

  @override
  State<PrescriptionDetailScreen> createState() => _PrescriptionDetailScreenState();
}

class _PrescriptionDetailScreenState extends State<PrescriptionDetailScreen> {
  dynamic _prescription;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getPrescriptionDetail(widget.prescriptionId);
      setState(() => _prescription = data);
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load')));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Prescription Detail')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_prescription['medicine']['name'] ?? '', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text('Dosage: ${_prescription['dosage'] ?? ''}'),
                  Text('Quantity: ${_prescription['quantity'] ?? ''}'),
                  Text('Status: ${_prescription['status'] ?? ''}'),
                  const SizedBox(height: 12),
                  Text('Notes:'),
                  Text(_prescription['notes'] ?? ''),
                ],
              ),
            ),
    );
  }
}
