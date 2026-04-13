// lib/domain/entities/employee_skill.dart

class EmployeeSkill {
  final String skillId;
  final int proficiency; // 0-5
  final DateTime lastAssessed;

  const EmployeeSkill({
    required this.skillId,
    required this.proficiency,
    required this.lastAssessed,
  });

  EmployeeSkill copyWith({
    String? skillId,
    int? proficiency,
    DateTime? lastAssessed,
  }) =>
      EmployeeSkill(
        skillId: skillId ?? this.skillId,
        proficiency: proficiency ?? this.proficiency,
        lastAssessed: lastAssessed ?? this.lastAssessed,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is EmployeeSkill && other.skillId == skillId;

  @override
  int get hashCode => skillId.hashCode;
}
