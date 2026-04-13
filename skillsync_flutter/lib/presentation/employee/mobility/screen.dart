// lib/presentation/employee/mobility/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _roleFitUc = const CalculateRoleFitUseCase();

class EmployeeMobilityScreen extends ConsumerWidget {
  const EmployeeMobilityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final employee = ref.watch(authProvider).currentUser;
    if (employee == null) return const LoadingView();

    final rolesAsync = ref.watch(employeeRolesProvider);

    return rolesAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (roles) {
        final openRoles = (roles as List<Role>)
            .where((r) => r.id != employee.roleId)
            .map((role) {
              final result = _roleFitUc.call(employee, role);
              return (role: role, fit: result.fitScore,
                  matching: result.matchingSkillIds.length,
                  missing: result.missingSkillIds.length);
            })
            .toList()
          ..sort((a, b) => b.fit.compareTo(a.fit));

        if (openRoles.isEmpty) {
          return const EmptyState(icon: Icons.swap_horiz_outlined, title: 'No other roles available');
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: openRoles.length + 1,
          itemBuilder: (ctx, i) {
            if (i == 0) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text('${openRoles.length} Open Positions',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              );
            }
            final item = openRoles[i - 1];
            final color = item.fit >= 75 ? AppColors.success : item.fit >= 50 ? AppColors.warning : AppColors.riskHigh;
            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(item.role.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      Text('${item.role.department} • ${item.role.levelLabel}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ])),
                    Text('${item.fit}%', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
                  ]),
                  const SizedBox(height: 10),
                  LinearProgressIndicator(value: item.fit / 100, backgroundColor: color.withOpacity(0.2), valueColor: AlwaysStoppedAnimation<Color>(color), minHeight: 6),
                  const SizedBox(height: 8),
                  Row(children: [
                    _Tag(label: '${item.matching} matching', color: AppColors.success),
                    const SizedBox(width: 8),
                    _Tag(label: '${item.missing} gaps', color: AppColors.riskHigh),
                  ]),
                ]),
              ),
            );
          },
        );
      },
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final Color color;
  const _Tag({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(12)),
      child: Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
