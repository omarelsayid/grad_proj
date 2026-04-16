// lib/services/auth_service.dart
// Wraps ApiClient auth calls and converts raw JSON → domain Employee entity.
import '../domain/entities/employee.dart';
import '../domain/entities/employee_skill.dart';
import 'api_client.dart';

class AuthResult {
  final Employee employee;
  final String   role;       // employee | manager | hr_admin
  final String   accessToken;
  final String   refreshToken;

  const AuthResult({
    required this.employee,
    required this.role,
    required this.accessToken,
    required this.refreshToken,
  });
}

class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  final _api = ApiClient.instance;

  Future<AuthResult> login(String email, String password) async {
    final data = await _api.login(email, password);
    return _parseResult(data);
  }

  Future<AuthResult> register(String email, String password, String name, String role) async {
    final data = await _api.register(email, password, name, role);
    return _parseResult(data);
  }

  Future<void> logout() => _api.logout();

  // ── Parse backend response → domain types ─────────────────────────────────
  AuthResult _parseResult(Map<String, dynamic> data) {
    final role = data['role'] as String? ?? 'employee';

    final empJson = data['employee'] as Map<String, dynamic>?;
    final employee = empJson != null ? _parseEmployee(empJson) : _fallbackEmployee(data);

    return AuthResult(
      employee:     employee,
      role:         role,
      accessToken:  data['accessToken'] as String,
      refreshToken: data['refreshToken'] as String,
    );
  }

  Employee _parseEmployee(Map<String, dynamic> e) {
    final skillsJson = e['skills'] as List<dynamic>? ?? [];
    return Employee(
      id:                e['id'] as String,
      name:              e['name'] as String,
      email:             e['email'] as String,
      avatarUrl:         e['avatarUrl'] as String? ?? '',
      currentRole:       e['currentRole'] as String,
      roleId:            e['roleId'] as String,
      department:        e['department'] as String,
      joinDate:          DateTime.parse(e['joinDate'] as String),
      salary:            (e['salary'] as num).toDouble(),
      phone:             e['phone'] as String? ?? '',
      commuteDistance:   e['commuteDistance'] as String? ?? 'moderate',
      satisfactionScore: (e['satisfactionScore'] as num).toDouble(),
      skills: skillsJson.map((s) {
        final sk = s as Map<String, dynamic>;
        return EmployeeSkill(
          skillId:      sk['skillId'] as String,
          proficiency:  (sk['proficiency'] as num).toInt(),
          lastAssessed: DateTime.parse(sk['lastAssessed'] as String),
        );
      }).toList(),
    );
  }

  // Fallback when no employee profile is linked yet (e.g. first-time register)
  Employee _fallbackEmployee(Map<String, dynamic> data) => Employee(
    id:                '',
    name:              '',
    email:             '',
    avatarUrl:         '',
    currentRole:       '',
    roleId:            '',
    department:        '',
    joinDate:          DateTime.now(),
    salary:            0,
    phone:             '',
    commuteDistance:   'moderate',
    satisfactionScore: 70,
    skills:            [],
  );
}
