import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/main_screen.dart';
import 'screens/prescription_detail_screen.dart';
import 'screens/prescription_trace_screen.dart';
import 'screens/medicine_detail_screen.dart';
import 'screens/enhanced_medicine_catalog_screen.dart';

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
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/main': (context) => const MainScreen(),
        '/medicines': (context) => const EnhancedMedicineCatalogScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/prescription') {
          final args = settings.arguments as Map<String, dynamic>?;
          return MaterialPageRoute(builder: (_) => PrescriptionDetailScreen(prescriptionId: args?['id'] ?? 0));
        }
        if (settings.name == '/prescription/trace') {
          final args = settings.arguments as Map<String, dynamic>?;
          return MaterialPageRoute(builder: (_) => PrescriptionTraceScreen(prescriptionId: args?['id'] ?? 0));
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