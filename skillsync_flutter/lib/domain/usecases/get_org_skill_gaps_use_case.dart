// lib/domain/usecases/get_org_skill_gaps_use_case.dart
import '../entities/employee.dart';
import '../entities/role.dart';
import '../entities/skill.dart';

class SkillGapEntry {
  final Skill skill;
  final int demand; // how many roles require it
  final double avgSupply; // avg proficiency across employees
  final double gapRatio; // demand / (avgSupply + 1) — higher = bigger gap

  const SkillGapEntry({
    required this.skill,
    required this.demand,
    required this.avgSupply,
    required this.gapRatio,
  });
}

class GetOrgSkillGapsUseCase {
  const GetOrgSkillGapsUseCase();

  List<SkillGapEntry> call({
    required List<Employee> employees,
    required List<Role> roles,
    required List<Skill> skills,
  }) {
    // Demand: count of roles requiring each skill
    final demand = <String, int>{};
    for (final role in roles) {
      for (final req in role.requiredSkills) {
        demand[req.skillId] = (demand[req.skillId] ?? 0) + 1;
      }
    }

    // Supply: avg proficiency per skill across employees
    final supplySum = <String, double>{};
    final supplyCount = <String, int>{};
    for (final emp in employees) {
      for (final es in emp.skills) {
        supplySum[es.skillId] = (supplySum[es.skillId] ?? 0) + es.proficiency;
        supplyCount[es.skillId] = (supplyCount[es.skillId] ?? 0) + 1;
      }
    }

    final entries = <SkillGapEntry>[];
    for (final skill in skills) {
      final d = demand[skill.id] ?? 0;
      if (d == 0) continue;
      final sum = supplySum[skill.id] ?? 0.0;
      final cnt = supplyCount[skill.id] ?? 0;
      final avgSupply = cnt > 0 ? sum / cnt : 0.0;
      entries.add(SkillGapEntry(
        skill: skill,
        demand: d,
        avgSupply: avgSupply,
        gapRatio: d / (avgSupply + 1),
      ));
    }

    entries.sort((a, b) => b.demand.compareTo(a.demand));
    return entries;
  }
}
