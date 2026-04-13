// lib/presentation/employee/skills/widgets/skill_chain_view.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../domain/entities/employee.dart';
import '../../../../domain/entities/skill.dart';
import '../../../../core/theme/app_colors.dart';

class SkillChainView extends ConsumerWidget {
  final Employee employee;
  final Map<String, Skill> skillMap;

  const SkillChainView({super.key, required this.employee, required this.skillMap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final employeeSkillIds = employee.skills.map((s) => s.skillId).toSet();

    final currentSkills = employee.skills
        .where((es) => es.proficiency >= 3)
        .map((es) => skillMap[es.skillId])
        .whereType<Skill>()
        .take(3)
        .toList();

    final developSkills = employee.skills
        .where((es) => es.proficiency > 0 && es.proficiency < 3)
        .map((es) => skillMap[es.skillId])
        .whereType<Skill>()
        .take(3)
        .toList();

    final nextSkills = skillMap.keys
        .toSet()
        .difference(employeeSkillIds)
        .map((id) => skillMap[id])
        .whereType<Skill>()
        .take(3)
        .toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: _ChainColumn(label: 'Strong', color: AppColors.success, skills: currentSkills)),
            const SizedBox(width: 8),
            const Icon(Icons.arrow_forward, color: Colors.grey, size: 20),
            const SizedBox(width: 8),
            Expanded(child: _ChainColumn(label: 'Develop', color: AppColors.warning, skills: developSkills)),
            const SizedBox(width: 8),
            const Icon(Icons.arrow_forward, color: Colors.grey, size: 20),
            const SizedBox(width: 8),
            Expanded(child: _ChainColumn(label: 'Next', color: AppColors.primary, skills: nextSkills)),
          ],
        ),
      ),
    );
  }
}

class _ChainColumn extends StatelessWidget {
  final String label;
  final Color color;
  final List<Skill> skills;

  const _ChainColumn({required this.label, required this.color, required this.skills});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(color: color.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
          child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
        ),
        const SizedBox(height: 8),
        if (skills.isEmpty)
          const Text('None', style: TextStyle(color: Colors.grey, fontSize: 12))
        else
          ...skills.map((s) => Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text(s.name, style: const TextStyle(fontSize: 12)),
          )),
      ],
    );
  }
}
