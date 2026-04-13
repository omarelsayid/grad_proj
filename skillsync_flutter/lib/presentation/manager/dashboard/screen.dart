// lib/presentation/manager/dashboard/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/widgets/stat_card.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/find_replacement_candidates_use_case.dart';
import '../../../domain/usecases/get_org_skill_gaps_use_case.dart';
import '../../auth/auth_provider.dart';
import '../../employee/dashboard/provider.dart';

final _roleFitUc = const CalculateRoleFitUseCase();
final _replacementUc = FindReplacementCandidatesUseCase(_roleFitUc);
final _skillGapsUc = const GetOrgSkillGapsUseCase();

class ManagerDashboardScreen extends ConsumerWidget {
  const ManagerDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) => skillsAsync.when(
          loading: () => const LoadingView(),
          error: (e, _) => Center(child: Text('$e')),
          data: (skills) {
            // Mock: manager manages first 10 employees
            final teamEmps = allEmps.take(10).toList();
            final gaps = _skillGapsUc.call(employees: teamEmps, roles: roles, skills: skills);

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                GridView.count(
                  crossAxisCount: 2, shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 8, crossAxisSpacing: 8, childAspectRatio: 2.4,
                  children: [
                    StatCard(label: 'Team Size', value: '${teamEmps.length}', icon: Icons.group, iconColor: AppColors.primary, onTap: () => context.go('/manager/team')),
                    StatCard(label: 'Departments', value: '${teamEmps.map((e) => e.department).toSet().length}', icon: Icons.account_tree, iconColor: AppColors.secondary, onTap: () => context.go('/manager/departments')),
                    StatCard(label: 'Skill Gaps', value: '${gaps.length}', icon: Icons.warning_outlined, iconColor: AppColors.warning, onTap: () => context.go('/manager/skills')),
                    StatCard(label: 'Open Roles', value: '${roles.length}', icon: Icons.badge_outlined, iconColor: AppColors.accent, onTap: () => context.go('/manager/roles')),
                  ],
                ),
                const SizedBox(height: 20),
                _buildSkillGaps(context, gaps),
                const SizedBox(height: 20),
                _buildReplacementCard(context, teamEmps, roles, skills),
              ]),
            );
          },
        ),
      ),
    );
  }

  Widget _buildSkillGaps(BuildContext context, List gaps) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Top Skill Gaps', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      ...gaps.take(4).map((g) => Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          leading: const Icon(Icons.psychology_outlined, color: AppColors.warning),
          title: Text(g.skill.name, style: const TextStyle(fontWeight: FontWeight.w500)),
          subtitle: Text('Demand: ${g.demand} roles • Avg supply: ${g.avgSupply.toStringAsFixed(1)}/5'),
          trailing: Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(color: AppColors.warning.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
            child: Text('Gap: ${g.gapRatio.toStringAsFixed(1)}', style: const TextStyle(color: AppColors.warning, fontWeight: FontWeight.bold, fontSize: 11)),
          ),
        ),
      )),
    ]);
  }

  Widget _buildReplacementCard(BuildContext context, List<Employee> teamEmps, List<Role> roles, List<Skill> skills) {
    if (teamEmps.isEmpty) return const SizedBox.shrink();
    final departing = teamEmps.first;
    final roleMap = {for (final r in roles) r.id: r};
    final role = roleMap[departing.roleId];
    if (role == null) return const SizedBox.shrink();
    final candidates = _replacementUc.call(
      departing: departing, allEmployees: teamEmps,
      role: role, allSkills: skills, limit: 3,
    );

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text('Replacement Preview', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        TextButton(onPressed: () => context.go('/manager/replacements'), child: const Text('Full view')),
      ]),
      ...candidates.take(3).map((c) => Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          leading: CircleAvatar(child: Text(c.employee.name[0])),
          title: Text(c.employee.name),
          subtitle: Text(c.employee.currentRole),
          trailing: Text('${c.fitScore}%', style: TextStyle(fontWeight: FontWeight.bold, color: c.fitScore > 60 ? AppColors.success : AppColors.warning, fontSize: 16)),
        ),
      )),
    ]);
  }
}
