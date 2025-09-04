import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/prescriptions_screen.dart';
import 'screens/prescription_detail_screen.dart';
import 'screens/medicine_list_screen.dart';
import 'screens/medicine_detail_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Patient App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/prescriptions': (context) => const PrescriptionsScreen(),
        '/medicines': (context) => const MedicineListScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/prescription') {
          final args = settings.arguments as Map<String, dynamic>?;
          return MaterialPageRoute(builder: (_) => PrescriptionDetailScreen(prescriptionId: args?['id'] ?? 0));
        }
        if (settings.name == '/medicine') {
          final args = settings.arguments as Map<String, dynamic>?;
          return MaterialPageRoute(builder: (_) => MedicineDetailScreen(medicineId: args?['id'] ?? 0));
        }
        return null;
      },
    );
  }
}
