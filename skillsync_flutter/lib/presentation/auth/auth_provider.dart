// lib/presentation/auth/auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/employee.dart';
import '../../data/repositories/mock_employee_repository.dart';
import '../../data/repositories/mock_skill_repository.dart';
import '../../domain/repositories/employee_repository.dart';
import '../../domain/repositories/skill_repository.dart';

// Repository providers (singletons)
final employeeRepositoryProvider = Provider<EmployeeRepository>(
  (_) => MockEmployeeRepository(),
);

final skillRepositoryProvider = Provider<SkillRepository>(
  (_) => MockSkillRepository(),
);

// Auth state
class AuthState {
  final Employee? currentUser;
  final String role; // employee | manager | hr_admin

  const AuthState({this.currentUser, this.role = 'employee'});

  bool get isAuthenticated => currentUser != null;

  AuthState copyWith({Employee? currentUser, String? role}) => AuthState(
        currentUser: currentUser ?? this.currentUser,
        role: role ?? this.role,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState());

  void login(Employee employee, String role) {
    state = AuthState(currentUser: employee, role: role);
  }

  void logout() {
    state = const AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (_) => AuthNotifier(),
);

// Theme toggle
final darkModeProvider = StateProvider<bool>((_) => false);
