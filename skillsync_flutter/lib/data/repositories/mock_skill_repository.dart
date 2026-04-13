// lib/data/repositories/mock_skill_repository.dart
import '../../domain/entities/skill.dart';
import '../../domain/entities/learning_item.dart';
import '../../domain/entities/skill_chain.dart';
import '../../domain/entities/role.dart';
import '../../domain/entities/holiday.dart';
import '../../domain/entities/audit_log.dart';
import '../../domain/repositories/skill_repository.dart';
import '../mock/mock_skills.dart';
import '../mock/mock_learning_items.dart';
import '../mock/mock_roles.dart';
import '../mock/mock_static_data.dart';

class MockSkillRepository implements SkillRepository {
  final List<Skill> _skills = List.from(mockSkills);
  final List<LearningItem> _learningItems = List.from(mockLearningItems);
  final List<Role> _roles = List.from(mockRoles);

  @override
  Future<List<Skill>> getAllSkills() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return List.unmodifiable(_skills);
  }

  @override
  Future<List<LearningItem>> getAllLearningItems() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return List.unmodifiable(_learningItems);
  }

  @override
  Future<List<SkillChain>> getSkillChains() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return mockSkillChains;
  }

  @override
  Future<List<Role>> getAllRoles() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return List.unmodifiable(_roles);
  }

  @override
  Future<Role?> getRoleById(String id) async {
    try {
      return _roles.firstWhere((r) => r.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<Role> addRole(Role role) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _roles.add(role);
    return role;
  }

  @override
  Future<Role> updateRole(Role role) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _roles.indexWhere((r) => r.id == role.id);
    if (idx != -1) _roles[idx] = role;
    return role;
  }

  @override
  Future<void> deleteRole(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _roles.removeWhere((r) => r.id == id);
  }

  @override
  Future<Skill> addSkill(Skill skill) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _skills.add(skill);
    return skill;
  }

  @override
  Future<Skill> updateSkill(Skill skill) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _skills.indexWhere((s) => s.id == skill.id);
    if (idx != -1) _skills[idx] = skill;
    return skill;
  }

  @override
  Future<void> deleteSkill(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _skills.removeWhere((s) => s.id == id);
  }

  @override
  Future<LearningItem> addLearningItem(LearningItem item) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _learningItems.add(item);
    return item;
  }

  @override
  Future<LearningItem> updateLearningItem(LearningItem item) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _learningItems.indexWhere((i) => i.id == item.id);
    if (idx != -1) _learningItems[idx] = item;
    return item;
  }

  @override
  Future<void> deleteLearningItem(String id) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _learningItems.removeWhere((i) => i.id == id);
  }

  @override
  Future<List<Holiday>> getHolidays() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return mockHolidays;
  }

  @override
  Future<List<AuditLog>> getAuditLogs() async {
    await Future.delayed(const Duration(milliseconds: 200));
    return mockAuditLogs;
  }
}
