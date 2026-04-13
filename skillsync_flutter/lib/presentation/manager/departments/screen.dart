// lib/presentation/manager/departments/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../employee/dashboard/provider.dart';

class ManagerDepartmentsScreen extends ConsumerWidget {
  const ManagerDepartmentsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        // Manager sees their team (first 10 employees)
        final teamEmps = allEmps.take(10).toList();

        // Group by department
        final deptMap = <String, List<Employee>>{};
        for (final emp in teamEmps) {
          deptMap[emp.department] ??= [];
          deptMap[emp.department]!.add(emp);
        }

        final departments = deptMap.entries.toList()
          ..sort((a, b) => b.value.length.compareTo(a.value.length));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: departments.length + 1,
          itemBuilder: (ctx, i) {
            if (i == 0) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  'Team Departments (${departments.length})',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              );
            }
            final entry = departments[i - 1];
            final dept = entry.key;
            final emps = entry.value;
            final avgTenure = emps
                .map((e) => e.tenureYears)
                .reduce((a, b) => a + b) / emps.length;

            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.account_tree_outlined, color: AppColors.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(dept, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      Text('${emps.length} member${emps.length == 1 ? '' : 's'}',
                          style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ])),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.secondary.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Avg ${avgTenure.toStringAsFixed(1)}y',
                        style: const TextStyle(fontSize: 12, color: AppColors.secondary, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ]),
                  const Divider(height: 20),
                  // Member avatars
                  Wrap(spacing: 6, runSpacing: 6,
                    children: emps.map((e) => Tooltip(
                      message: '${e.name} — ${e.currentRole}',
                      child: CircleAvatar(
                        radius: 16,
                        backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                        child: Text(e.name[0], style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.bold)),
                      ),
                    )).toList(),
                  ),
                  const SizedBox(height: 10),
                  // Role breakdown
                  ...emps.map((e) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(children: [
                      const Icon(Icons.person_outline, size: 14, color: Colors.grey),
                      const SizedBox(width: 4),
                      Expanded(child: Text(e.name, style: const TextStyle(fontSize: 12))),
                      Text(e.currentRole, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ]),
                  )),
                ]),
              ),
            );
          },
        );
      },
    );
  }
}
