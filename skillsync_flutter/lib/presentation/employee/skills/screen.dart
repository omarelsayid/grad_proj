// lib/presentation/employee/skills/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/proficiency_bar.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';
import 'widgets/skill_chain_view.dart';

final _roleFitUc = const CalculateRoleFitUseCase();

class EmployeeSkillsScreen extends ConsumerWidget {
  const EmployeeSkillsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final employee = ref.watch(authProvider).currentUser;
    if (employee == null) return const LoadingView();

    final skillsAsync = ref.watch(employeeSkillsProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);

    return skillsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allSkills) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) {
          final skillMap = {for (final s in allSkills as List<Skill>) s.id: s};
          final roleMap = {for (final r in roles as List<Role>) r.id: r};
          final currentRole = roleMap[employee.roleId];
          final fitResult = currentRole != null
              ? _roleFitUc.call(employee, currentRole)
              : null;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (currentRole != null && fitResult != null) ...[
                  _buildRoleFitCard(context, currentRole, fitResult),
                  const SizedBox(height: 20),
                ],
                Text('My Skills (${employee.skills.length})',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                if (employee.skills.isEmpty)
                  const EmptyState(icon: Icons.psychology_outlined, title: 'No skills recorded yet')
                else
                  ...employee.skills.map((es) {
                    final skill = skillMap[es.skillId];
                    if (skill == null) return const SizedBox.shrink();
                    return _SkillCard(skill: skill, proficiency: es.proficiency);
                  }),
                if (currentRole != null) ...[
                  const SizedBox(height: 24),
                  Text('Skill Chain',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  SkillChainView(employee: employee, skillMap: skillMap),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildRoleFitCard(BuildContext context, Role role, RoleFitResult fitResult) {
    final color = fitResult.fitScore >= 75 ? AppColors.success
        : fitResult.fitScore >= 50 ? AppColors.warning : AppColors.riskHigh;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.analytics_outlined, color: AppColors.primary),
              const SizedBox(width: 8),
              Text('Role Fit — ${role.title}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            ]),
            const SizedBox(height: 12),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('${fitResult.fitScore}%', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text('${fitResult.matchingSkillIds.length} matching', style: const TextStyle(color: AppColors.success, fontSize: 12)),
                Text('${fitResult.missingSkillIds.length} gaps', style: const TextStyle(color: AppColors.riskHigh, fontSize: 12)),
              ]),
            ]),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: fitResult.fitScore / 100,
              backgroundColor: color.withOpacity(0.2),
              valueColor: AlwaysStoppedAnimation<Color>(color),
              minHeight: 8,
            ),
          ],
        ),
      ),
    );
  }
}

class _SkillCard extends StatelessWidget {
  final Skill skill;
  final int proficiency;

  const _SkillCard({required this.skill, required this.proficiency});

  Color get _categoryColor {
    switch (skill.category) {
      case SkillCategory.technical: return AppColors.skillTechnical;
      case SkillCategory.soft: return AppColors.skillSoft;
      case SkillCategory.management: return AppColors.skillManagement;
      case SkillCategory.domain: return AppColors.skillDomain;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Expanded(child: Text(skill.name, style: const TextStyle(fontWeight: FontWeight.w600))),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _categoryColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(skill.category.name, style: TextStyle(color: _categoryColor, fontSize: 11, fontWeight: FontWeight.w600)),
              ),
            ]),
            const SizedBox(height: 8),
            ProficiencyBar(proficiency: proficiency),
          ],
        ),
      ),
    );
  }
}
