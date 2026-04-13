// lib/presentation/hr/leaves/screen.dart
import 'package:flutter/material.dart';
import '../../manager/leaves/screen.dart';

// HR leaves screen reuses manager leaves with full access
class HrLeavesScreen extends StatelessWidget {
  const HrLeavesScreen({super.key});
  @override
  Widget build(BuildContext context) => const ManagerLeavesScreen();
}
