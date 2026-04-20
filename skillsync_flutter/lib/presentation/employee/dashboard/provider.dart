// lib/presentation/employee/dashboard/provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/entities/role.dart';
import '../../auth/auth_provider.dart';

// Shared selected target role — drives both Skill Gap panel and Learning page
final selectedTargetRoleProvider = StateProvider<String?>((ref) => null);

final employeeSkillsProvider = FutureProvider<List<Skill>>((ref) async {
  final repo = ref.read(skillRepositoryProvider);
  return repo.getAllSkills();
});

final employeeRolesProvider = FutureProvider<List<Role>>((ref) async {
  final repo = ref.read(skillRepositoryProvider);
  return repo.getAllRoles();
});

final employeeLeaveBalanceProvider = FutureProvider((ref) async {
  final auth = ref.read(authProvider);
  final repo = ref.read(employeeRepositoryProvider);
  final emp = auth.currentUser;
  if (emp == null) throw Exception('Not authenticated');
  final balance = await repo.getLeaveBalance(emp.id);
  return balance;
});

final employeeTodosProvider = FutureProvider((ref) async {
  final auth = ref.read(authProvider);
  final repo = ref.read(employeeRepositoryProvider);
  final emp = auth.currentUser;
  if (emp == null) return [];
  return repo.getTodos(emp.id);
});

final allEmployeesProvider = FutureProvider((ref) async {
  final repo = ref.read(employeeRepositoryProvider);
  return repo.getAll();
});
