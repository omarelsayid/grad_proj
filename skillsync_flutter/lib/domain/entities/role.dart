// lib/domain/entities/role.dart

enum RoleLevel { junior, mid, senior, lead, manager }

class RoleSkillRequirement {
  final String skillId;
  final int minProficiency;

  const RoleSkillRequirement({
    required this.skillId,
    required this.minProficiency,
  });
}

class Role {
  final String id;
  final String title;
  final String department;
  final RoleLevel level;
  final String description;
  final List<RoleSkillRequirement> requiredSkills;

  const Role({
    required this.id,
    required this.title,
    required this.department,
    required this.level,
    required this.description,
    required this.requiredSkills,
  });

  Role copyWith({
    String? id,
    String? title,
    String? department,
    RoleLevel? level,
    String? description,
    List<RoleSkillRequirement>? requiredSkills,
  }) =>
      Role(
        id: id ?? this.id,
        title: title ?? this.title,
        department: department ?? this.department,
        level: level ?? this.level,
        description: description ?? this.description,
        requiredSkills: requiredSkills ?? this.requiredSkills,
      );

  String get levelLabel {
    switch (level) {
      case RoleLevel.junior: return 'Junior';
      case RoleLevel.mid: return 'Mid';
      case RoleLevel.senior: return 'Senior';
      case RoleLevel.lead: return 'Lead';
      case RoleLevel.manager: return 'Manager';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Role && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
