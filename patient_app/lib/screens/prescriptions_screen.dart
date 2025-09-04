import 'package:flutter/material.dart';
import '../services/api_service.dart';

class PrescriptionsScreen extends StatefulWidget {
  const PrescriptionsScreen({super.key});

  @override
  State<PrescriptionsScreen> createState() => _PrescriptionsScreenState();
}

class _PrescriptionsScreenState extends State<PrescriptionsScreen> {
  List<dynamic> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getPrescriptions();
      setState(() {
        _items = data['results'] ?? [];
      });
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load')));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Prescriptions')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async => _load(),
              child: ListView.builder(
                itemCount: _items.length,
                itemBuilder: (context, index) {
                  final p = _items[index];
                  return ListTile(
                    title: Text(p['medicine']['name'] ?? 'Medicine'),
                    subtitle: Text('${p['dosage']} • ${p['quantity']} units'),
                    trailing: Text(p['status'] ?? ''),
                    onTap: () => Navigator.pushNamed(context, '/prescription', arguments: {'id': p['id']}),
                  );
                },
              ),
            ),
    );
  }
}
