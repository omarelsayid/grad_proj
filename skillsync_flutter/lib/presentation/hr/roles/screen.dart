// lib/presentation/hr/roles/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/skill.dart';
import '../../employee/dashboard/provider.dart';

class HrRolesScreen extends ConsumerWidget {
  const HrRolesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rolesAsync = ref.watch(employeeRolesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);

    return rolesAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (roles) => skillsAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (skills) {
          final skillMap = {for (final s in skills as List<Skill>) s.id: s};
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: (roles as List<Role>).length + 1,
            itemBuilder: (ctx, i) {
              if (i == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text('${roles.length} Roles',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                );
              }
              final role = roles[i - 1];
              return _RoleCard(role: role, skillMap: skillMap);
            },
          );
        },
      ),
    );
  }
}

class _RoleCard extends StatelessWidget {
  final Role role;
  final Map<String, Skill> skillMap;
  const _RoleCard({required this.role, required this.skillMap});

  Color get _levelColor {
    switch (role.level) {
      case RoleLevel.junior: return AppColors.success;
      case RoleLevel.mid: return AppColors.primary;
      case RoleLevel.senior: return AppColors.warning;
      case RoleLevel.lead: return AppColors.riskHigh;
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
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(role.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              Text(role.department, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ])),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: _levelColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16)),
              child: Text(role.levelLabel, style: TextStyle(color: _levelColor, fontWeight: FontWeight.bold, fontSize: 12)),
            ),
          ]),
          if (role.description.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(role.description, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
          if (role.requiredSkills.isNotEmpty) ...[
            const SizedBox(height: 10),
            const Text('Required Skills:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Wrap(spacing: 6, runSpacing: 4, children: role.requiredSkills.map((req) {
              final skill = skillMap[req.skillId];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: AppColors.primary.withValues(alpha: 0.08), borderRadius: BorderRadius.circular(12)),
                child: Text('${skill?.name ?? req.skillId} (L${req.minProficiency})', style: const TextStyle(fontSize: 11, color: AppColors.primary)),
              );
            }).toList()),
          ],
        ]),
      ),
    );
  }
}
