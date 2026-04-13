// lib/domain/entities/skill.dart

enum SkillCategory { technical, soft, management, domain }

class Skill {
  final String id;
  final String name;
  final SkillCategory category;
  final String description;
  final List<String> relatedSkillIds;

  const Skill({
    required this.id,
    required this.name,
    required this.category,
    required this.description,
    this.relatedSkillIds = const [],
  });

  Skill copyWith({
    String? id,
    String? name,
    SkillCategory? category,
    String? description,
    List<String>? relatedSkillIds,
  }) =>
      Skill(
        id: id ?? this.id,
        name: name ?? this.name,
        category: category ?? this.category,
        description: description ?? this.description,
        relatedSkillIds: relatedSkillIds ?? this.relatedSkillIds,
      );

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Skill && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
