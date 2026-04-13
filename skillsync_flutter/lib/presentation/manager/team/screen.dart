// lib/presentation/manager/team/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/skill.dart';
import '../../employee/dashboard/provider.dart';

class ManagerTeamScreen extends ConsumerWidget {
  const ManagerTeamScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) => skillsAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (allSkills) {
          final teamEmps = (allEmps as List<Employee>).take(10).toList();
          final skillMap = {for (final s in allSkills as List<Skill>) s.id: s};

          if (teamEmps.isEmpty) {
            return const EmptyState(icon: Icons.group_outlined, title: 'No team members');
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: teamEmps.length + 1,
            itemBuilder: (ctx, i) {
              if (i == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text('Team (${teamEmps.length} members)',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                );
              }
              final emp = teamEmps[i - 1];
              final topSkills = emp.skills
                  .where((es) => es.proficiency >= 3)
                  .take(3)
                  .map((es) => skillMap[es.skillId]?.name ?? es.skillId)
                  .toList();

              return Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        CircleAvatar(
                          backgroundColor: AppColors.primary.withOpacity(0.15),
                          child: Text(emp.name[0], style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(emp.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text('${emp.currentRole} • ${emp.department}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                        ])),
                        Text('${(DateTime.now().difference(emp.joinDate).inDays / 365).toStringAsFixed(1)}y', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      ]),
                      if (topSkills.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 6, runSpacing: 4,
                          children: topSkills.map((s) => Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.08),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(s, style: const TextStyle(fontSize: 11, color: AppColors.primary)),
                          )).toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
