import 'package:flutter/material.dart';
import '../services/api_service.dart';

class MedicineListScreen extends StatefulWidget {
  const MedicineListScreen({super.key});

  @override
  State<MedicineListScreen> createState() => _MedicineListScreenState();
}

class _MedicineListScreenState extends State<MedicineListScreen> {
  List<dynamic> _items = [];
  List<dynamic> _categories = [];
  bool _loading = true;
  String _search = '';
  String _selectedCategory = '';

  @override
  void initState() {
    super.initState();
    _loadCategories();
    _loadMedicines();
  }

  void _loadCategories() {
    // In a real app, this would come from an API endpoint
    // For now, we'll use the categories from the web app
    setState(() {
      _categories = [
        {'id': 'pain_relief', 'name': 'Pain Relief'},
        {'id': 'antibiotics', 'name': 'Antibiotics'},
        {'id': 'cardiovascular', 'name': 'Cardiovascular'},
        {'id': 'diabetes', 'name': 'Diabetes'},
        {'id': 'respiratory', 'name': 'Respiratory'},
        {'id': 'gastrointestinal', 'name': 'Gastrointestinal'},
        {'id': 'vitamins', 'name': 'Vitamins & Supplements'},
        {'id': 'skin_care', 'name': 'Skin Care'},
        {'id': 'other', 'name': 'Other'},
      ];
    });
  }

  void _loadMedicines() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getMedicines(search: _search, category: _selectedCategory);
      setState(() => _items = data['results'] ?? []);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load medicines')));
    } finally {
      setState(() => _loading = false);
    }
  }

  void _onSearchChanged(String value) {
    setState(() {
      _search = value;
    });
    // Debounce the search
    Future.delayed(const Duration(milliseconds: 500), () {
      if (_search == value) {
        _loadMedicines();
      }
    });
  }

  void _onCategorySelected(String? category) {
    setState(() {
      _selectedCategory = category ?? '';
      _loadMedicines();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Medicine Catalog'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadMedicines,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search and Filter Section
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                // Search Field
                TextField(
                  decoration: const InputDecoration(
                    labelText: 'Search medicines',
                    border: OutlineInputBorder(),
                    suffixIcon: Icon(Icons.search),
                  ),
                  onChanged: _onSearchChanged,
                ),
                const SizedBox(height: 10),
                // Category Filter
                SizedBox(
                  height: 40,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      FilterChip(
                        label: const Text('All'),
                        selected: _selectedCategory.isEmpty,
                        onSelected: (_) => _onCategorySelected(null),
                      ),
                      const SizedBox(width: 8),
                      ..._categories.map((category) {
                        return Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: FilterChip(
                            label: Text(category['name']),
                            selected: _selectedCategory == category['id'],
                            onSelected: (_) => _onCategorySelected(category['id']),
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Medicine List
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: () async => _loadMedicines(),
                    child: _items.isEmpty
                        ? const Center(child: Text('No medicines found'))
                        : GridView.builder(
                            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              childAspectRatio: 0.8,
                              crossAxisSpacing: 10,
                              mainAxisSpacing: 10,
                            ),
                            itemCount: _items.length,
                            itemBuilder: (context, index) {
                              final medicine = _items[index];
                              return _buildMedicineCard(medicine);
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicineCard(dynamic medicine) {
    return Card(
      elevation: 3,
      child: InkWell(
        onTap: () => Navigator.pushNamed(context, '/medicine', arguments: {'id': medicine['id']}),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Medicine Image
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  image: medicine['image'] != null
                      ? DecorationImage(
                          image: NetworkImage(medicine['image']),
                          fit: BoxFit.cover,
                        )
                      : null,
                ),
                child: medicine['image'] == null
                    ? const Icon(Icons.medical_services, size: 50, color: Colors.grey)
                    : null,
              ),
            ),
            // Medicine Info
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Medicine Name
                  Text(
                    medicine['name'] ?? '',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  // Generic Name
                  if (medicine['generic_name'] != null && medicine['generic_name'].toString().isNotEmpty)
                    Text(
                      medicine['generic_name'],
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  const SizedBox(height: 4),
                  // Strength and Form
                  if ((medicine['strength'] != null && medicine['strength'].toString().isNotEmpty) ||
                      (medicine['dosage_form'] != null && medicine['dosage_form'].toString().isNotEmpty))
                    Text(
                      '${medicine['strength'] ?? ''} ${medicine['dosage_form'] != null ? '• ${medicine['dosage_form']}' : ''}',
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  const SizedBox(height: 8),
                  // Category Badge
                  if (medicine['category'] != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.blue[100],
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        _getCategoryName(medicine['category']),
                        style: const TextStyle(fontSize: 10, color: Colors.blue),
                      ),
                    ),
                  const SizedBox(height: 8),
                  // Availability and Price
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // Availability
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: medicine['is_active'] == true ? Colors.green[100] : Colors.red[100],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          medicine['is_active'] == true ? 'In Stock' : 'Out of Stock',
                          style: TextStyle(
                            fontSize: 10,
                            color: medicine['is_active'] == true ? Colors.green[800] : Colors.red[800],
                          ),
                        ),
                      ),
                      // Price (if available in future API enhancements)
                      // const Text('\$12.99', style: TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getCategoryName(String categoryId) {
    final category = _categories.firstWhere(
      (cat) => cat['id'] == categoryId,
      orElse: () => {'name': 'Other'},
    );
    return category['name'];
  }
}