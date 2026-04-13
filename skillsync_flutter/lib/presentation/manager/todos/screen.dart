// lib/presentation/manager/todos/screen.dart
import 'package:flutter/material.dart';
import '../../employee/todos/screen.dart';

// Manager todos reuse the exact same implementation
class ManagerTodosScreen extends StatelessWidget {
  const ManagerTodosScreen({super.key});

  @override
  Widget build(BuildContext context) => const EmployeeTodosScreen();
}
