// lib/data/repositories/api_skill_repository.dart
import '../../domain/entities/audit_log.dart';
import '../../domain/entities/holiday.dart';
import '../../domain/entities/learning_item.dart';
import '../../domain/entities/role.dart';
import '../../domain/entities/skill.dart';
import '../../domain/entities/skill_chain.dart';
import '../../domain/repositories/skill_repository.dart';
import '../../services/api_client.dart';
import '../mock/mock_learning_items.dart';

class ApiSkillRepository implements SkillRepository {
  final ApiClient _api = ApiClient.instance;

  // ── Parsing helpers ──────────────────────────────────────────────────────────

  Skill _parseSkill(Map<String, dynamic> j) {
    SkillCategory parseCategory(String s) {
      switch (s) {
        case 'management': return SkillCategory.management;
        case 'soft':       return SkillCategory.soft;
        case 'domain':     return SkillCategory.domain;
        default:           return SkillCategory.technical;
      }
    }
    return Skill(
      id:              j['id'] as String,
      name:            j['name'] as String,
      category:        parseCategory(j['category'] as String? ?? 'technical'),
      description:     j['description'] as String? ?? '',
      relatedSkillIds: const [],
    );
  }

  Role _parseRole(Map<String, dynamic> j) {
    RoleLevel parseLevel(String s) {
      switch (s) {
        case 'junior':  return RoleLevel.junior;
        case 'mid':     return RoleLevel.mid;
        case 'senior':  return RoleLevel.senior;
        case 'lead':    return RoleLevel.lead;
        default:        return RoleLevel.manager;
      }
    }
    final rawReqs = j['requiredSkills'] as List<dynamic>? ?? [];
    return Role(
      id:          j['id'] as String,
      title:       j['title'] as String,
      department:  j['department'] as String,
      level:       parseLevel(j['level'] as String? ?? 'mid'),
      description: j['description'] as String? ?? '',
      requiredSkills: rawReqs.map((r) {
        final req = r as Map<String, dynamic>;
        return RoleSkillRequirement(
          skillId:        req['skillId'] as String? ?? req['skill_id'] as String,
          minProficiency: (req['minProficiency'] as num? ?? req['min_proficiency'] as num).toInt(),
        );
      }).toList(),
    );
  }

  SkillChain _parseSkillChain(Map<String, dynamic> j) {
    return SkillChain(
      fromSkillId: j['fromSkillId'] as String? ?? j['from_skill_id'] as String,
      toSkillId:   j['toSkillId'] as String? ?? j['to_skill_id'] as String,
      description: j['description'] as String? ?? '',
    );
  }

  Holiday _parseHoliday(Map<String, dynamic> j) {
    HolidayType parseType(String s) {
      switch (s) {
        case 'company':  return HolidayType.company;
        case 'optional': return HolidayType.optional;
        default:         return HolidayType.public;
      }
    }
    return Holiday(
      id:   j['id'] as String,
      name: j['name'] as String,
      date: DateTime.parse(j['date'] as String),
      type: parseType(j['type'] as String? ?? 'public'),
    );
  }

  AuditLog _parseAuditLog(Map<String, dynamic> j) {
    return AuditLog(
      id:          j['id'] as String,
      action:      j['action'] as String,
      entityType:  j['entityType'] as String? ?? j['entity_type'] as String? ?? '',
      entityId:    j['entityId'] as String? ?? j['entity_id'] as String? ?? '',
      performedBy: j['userId'] as String? ?? j['user_id'] as String? ?? 'system',
      timestamp:   DateTime.parse(j['createdAt'] as String? ?? j['created_at'] as String? ?? DateTime.now().toIso8601String()),
      details:     (j['newValues'] as Map<String, dynamic>?) ?? {},
    );
  }

  // ── SkillRepository implementation ──────────────────────────────────────────

  @override
  Future<List<Skill>> getAllSkills() async {
    final list = await _api.getSkills();
    return list.map((e) => _parseSkill(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<SkillChain>> getSkillChains() async {
    final list = await _api.getSkillChains();
    return list.map((e) => _parseSkillChain(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<Role>> getAllRoles() async {
    final list = await _api.getRoles();
    return list.map((e) => _parseRole(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<Role?> getRoleById(String id) async {
    try {
      final data = await _api.getRoleById(id);
      return _parseRole(data);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  @override
  Future<List<Holiday>> getHolidays() async {
    final list = await _api.getHolidays();
    return list.map((e) => _parseHoliday(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<AuditLog>> getAuditLogs() async {
    final list = await _api.getAuditLog();
    return list.map((e) => _parseAuditLog(e as Map<String, dynamic>)).toList();
  }

  // Learning items — no backend endpoint yet, use mock data
  @override
  Future<List<LearningItem>> getAllLearningItems() async => mockLearningItems;

  @override
  Future<LearningItem> addLearningItem(LearningItem item) async => item;

  @override
  Future<LearningItem> updateLearningItem(LearningItem item) async => item;

  @override
  Future<void> deleteLearningItem(String id) async {}

  // Role mutations
  @override
  Future<Role> addRole(Role role) async {
    final data = await _api.createRole({
      'id':          role.id,
      'title':       role.title,
      'department':  role.department,
      'level':       role.level.name,
      'description': role.description,
      'requiredSkills': role.requiredSkills.map((r) => {
        'skillId': r.skillId, 'minProficiency': r.minProficiency,
      }).toList(),
    });
    return _parseRole(data);
  }

  @override
  Future<Role> updateRole(Role role) async {
    final data = await _api.updateRole(role.id, {
      'title':       role.title,
      'department':  role.department,
      'level':       role.level.name,
      'description': role.description,
    });
    return _parseRole(data);
  }

  @override
  Future<void> deleteRole(String id) => _api.deleteRole(id);

  // Skill mutations
  @override
  Future<Skill> addSkill(Skill skill) async {
    final data = await _api.createSkill({
      'id':          skill.id,
      'name':        skill.name,
      'category':    skill.category.name,
      'description': skill.description,
    });
    return _parseSkill(data);
  }

  @override
  Future<Skill> updateSkill(Skill skill) async {
    final data = await _api.updateSkill(skill.id, {
      'name':        skill.name,
      'category':    skill.category.name,
      'description': skill.description,
    });
    return _parseSkill(data);
  }

  @override
  Future<void> deleteSkill(String id) => _api.deleteSkill(id);
}
