// lib/domain/repositories/skill_repository.dart
import '../entities/skill.dart';
import '../entities/learning_item.dart';
import '../entities/skill_chain.dart';
import '../entities/role.dart';
import '../entities/holiday.dart';
import '../entities/audit_log.dart';

abstract class SkillRepository {
  Future<List<Skill>> getAllSkills();
  Future<List<LearningItem>> getAllLearningItems();
  Future<List<SkillChain>> getSkillChains();
  Future<List<Role>> getAllRoles();
  Future<Role?> getRoleById(String id);
  Future<Role> addRole(Role role);
  Future<Role> updateRole(Role role);
  Future<void> deleteRole(String id);
  Future<Skill> addSkill(Skill skill);
  Future<Skill> updateSkill(Skill skill);
  Future<void> deleteSkill(String id);
  Future<LearningItem> addLearningItem(LearningItem item);
  Future<LearningItem> updateLearningItem(LearningItem item);
  Future<void> deleteLearningItem(String id);
  Future<List<Holiday>> getHolidays();
  Future<List<AuditLog>> getAuditLogs();
}
