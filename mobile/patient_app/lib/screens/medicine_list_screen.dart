import 'package:flutter/material.dart';
import '../services/api_service.dart';

class MedicineListScreen extends StatefulWidget {
  const MedicineListScreen({super.key});

  @override
  State<MedicineListScreen> createState() => _MedicineListScreenState();
}

class _MedicineListScreenState extends State<MedicineListScreen> {
  List<dynamic> _items = [];
  bool _loading = true;
  String _search = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getMedicines(search: _search);
      setState(() => _items = data['results'] ?? []);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load medicines')));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Medicines')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              decoration: const InputDecoration(labelText: 'Search'),
              onChanged: (v) => _search = v,
              onSubmitted: (v) => _load(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _items.length,
                    itemBuilder: (context, index) {
                      final m = _items[index];
                      return ListTile(
                        title: Text(m['name'] ?? ''),
                        subtitle: Text(m['generic_name'] ?? ''),
                        onTap: () => Navigator.pushNamed(context, '/medicine', arguments: {'id': m['id']}),
                      );
                    },
                  ),
          ),
        FloatingActionButton(child: Text("my prescription"),
         onPressed: (){
Navigator.pushReplacementNamed(context, '/prescriptions');
        }),
        ],
      ),
    );
  }
}
