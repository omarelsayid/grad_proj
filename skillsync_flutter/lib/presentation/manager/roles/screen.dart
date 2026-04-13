// lib/presentation/manager/roles/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/skill.dart';
import '../../employee/dashboard/provider.dart';

class ManagerRolesScreen extends ConsumerWidget {
  const ManagerRolesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rolesAsync = ref.watch(employeeRolesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);
    final empsAsync = ref.watch(allEmployeesProvider);

    return rolesAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (roles) => skillsAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (skills) => empsAsync.when(
          loading: () => const LoadingView(),
          error: (e, _) => Center(child: Text('$e')),
          data: (allEmps) {
            final skillMap = {for (final s in skills) s.id: s};
            final teamEmps = allEmps.take(10).toList();
            // Count how many team members are in each role
            final roleHeadcount = <String, int>{};
            for (final emp in teamEmps) {
              roleHeadcount[emp.roleId] = (roleHeadcount[emp.roleId] ?? 0) + 1;
            }

            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: roles.length + 1,
              itemBuilder: (ctx, i) {
                if (i == 0) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(
                      '${roles.length} Open Roles',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                  );
                }
                final role = roles[i - 1];
                final headcount = roleHeadcount[role.id] ?? 0;
                return _ManagerRoleCard(role: role, skillMap: skillMap, headcount: headcount);
              },
            );
          },
        ),
      ),
    );
  }
}

class _ManagerRoleCard extends StatelessWidget {
  final Role role;
  final Map<String, Skill> skillMap;
  final int headcount;

  const _ManagerRoleCard({required this.role, required this.skillMap, required this.headcount});

  Color get _levelColor {
    switch (role.level) {
      case RoleLevel.junior:  return AppColors.success;
      case RoleLevel.mid:     return AppColors.primary;
      case RoleLevel.senior:  return AppColors.warning;
      case RoleLevel.lead:    return AppColors.riskHigh;
      case RoleLevel.manager: return AppColors.riskCritical;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(
                color: _levelColor.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.badge_outlined, color: _levelColor, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(role.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              Text(role.department, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ])),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _levelColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(role.levelLabel,
                  style: TextStyle(color: _levelColor, fontWeight: FontWeight.bold, fontSize: 11)),
              ),
              const SizedBox(height: 4),
              Text('$headcount on team',
                style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ]),
          ]),
          if (role.description.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(role.description,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
              maxLines: 2, overflow: TextOverflow.ellipsis),
          ],
          if (role.requiredSkills.isNotEmpty) ...[
            const SizedBox(height: 10),
            const Text('Required Skills:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Wrap(spacing: 6, runSpacing: 4,
              children: role.requiredSkills.map((req) {
                final skill = skillMap[req.skillId];
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${skill?.name ?? req.skillId} · L${req.minProficiency}',
                    style: const TextStyle(fontSize: 11, color: AppColors.primary),
                  ),
                );
              }).toList(),
            ),
          ],
        ]),
      ),
    );
  }
}
