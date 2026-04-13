// lib/domain/entities/skill_chain.dart

class SkillChain {
  final String fromSkillId;
  final String toSkillId;
  final String description;

  const SkillChain({
    required this.fromSkillId,
    required this.toSkillId,
    required this.description,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SkillChain &&
          other.fromSkillId == fromSkillId &&
          other.toSkillId == toSkillId;

  @override
  int get hashCode => Object.hash(fromSkillId, toSkillId);
}
