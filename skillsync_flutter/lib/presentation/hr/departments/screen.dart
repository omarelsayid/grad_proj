// lib/presentation/hr/departments/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../employee/dashboard/provider.dart';

class HrDepartmentsScreen extends ConsumerWidget {
  const HrDepartmentsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final employees = allEmps as List<Employee>;

        // Group by department
        final deptMap = <String, List<Employee>>{};
        for (final emp in employees) {
          deptMap[emp.department] ??= [];
          deptMap[emp.department]!.add(emp);
        }

        final departments = deptMap.entries.toList()..sort((a, b) => b.value.length.compareTo(a.value.length));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: departments.length + 1,
          itemBuilder: (ctx, i) {
            if (i == 0) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text('${departments.length} Departments',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              );
            }
            final entry = departments[i - 1];
            final dept = entry.key;
            final emps = entry.value;
            final manager = emps.firstWhere((e) => e.currentRole.contains('Manager') || e.currentRole.contains('Lead'), orElse: () => emps.first);

            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(color: AppColors.primary.withOpacity(0.12), borderRadius: BorderRadius.circular(10)),
                      child: const Icon(Icons.account_tree_outlined, color: AppColors.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(dept, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      Text('${emps.length} employees', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ])),
                  ]),
                  const Divider(height: 20),
                  Row(children: [
                    const Icon(Icons.person_outlined, size: 16, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text('Manager: ${manager.name}', style: const TextStyle(fontSize: 13)),
                  ]),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 4, runSpacing: 4,
                    children: emps.take(5).map((e) => CircleAvatar(
                      radius: 14,
                      backgroundColor: AppColors.secondary.withOpacity(0.2),
                      child: Text(e.name[0], style: const TextStyle(fontSize: 11, color: AppColors.secondary)),
                    )).toList(),
                  ),
                ]),
              ),
            );
          },
        );
      },
    );
  }
}
