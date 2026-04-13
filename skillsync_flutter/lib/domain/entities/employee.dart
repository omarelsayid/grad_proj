// lib/domain/entities/employee.dart
import 'employee_skill.dart';

class Employee {
  final String id;
  final String name;
  final String email;
  final String avatarUrl;
  final String currentRole;
  final String roleId;
  final String department;
  final DateTime joinDate;
  final double salary;
  final String phone;
  final List<EmployeeSkill> skills;
  final String commuteDistance; // near | moderate | far | very_far
  final double satisfactionScore; // 0-100

  const Employee({
    required this.id,
    required this.name,
    required this.email,
    required this.avatarUrl,
    required this.currentRole,
    required this.roleId,
    required this.department,
    required this.joinDate,
    required this.salary,
    required this.phone,
    required this.skills,
    required this.commuteDistance,
    required this.satisfactionScore,
  });

  Employee copyWith({
    String? id,
    String? name,
    String? email,
    String? avatarUrl,
    String? currentRole,
    String? roleId,
    String? department,
    DateTime? joinDate,
    double? salary,
    String? phone,
    List<EmployeeSkill>? skills,
    String? commuteDistance,
    double? satisfactionScore,
  }) =>
      Employee(
        id: id ?? this.id,
        name: name ?? this.name,
        email: email ?? this.email,
        avatarUrl: avatarUrl ?? this.avatarUrl,
        currentRole: currentRole ?? this.currentRole,
        roleId: roleId ?? this.roleId,
        department: department ?? this.department,
        joinDate: joinDate ?? this.joinDate,
        salary: salary ?? this.salary,
        phone: phone ?? this.phone,
        skills: skills ?? this.skills,
        commuteDistance: commuteDistance ?? this.commuteDistance,
        satisfactionScore: satisfactionScore ?? this.satisfactionScore,
      );

  double get tenureYears {
    final diff = DateTime.now().difference(joinDate);
    return diff.inDays / 365.0;
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Employee && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
