// lib/presentation/hr/attendance/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../domain/entities/employee.dart';
import '../../../data/mock/mock_attendance.dart';
import '../../employee/dashboard/provider.dart';

class HrAttendanceScreen extends ConsumerStatefulWidget {
  const HrAttendanceScreen({super.key});
  @override ConsumerState<HrAttendanceScreen> createState() => _State();
}

class _State extends ConsumerState<HrAttendanceScreen> {
  String _deptFilter = 'All';

  @override
  Widget build(BuildContext context) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final employees = allEmps as List<Employee>;
        final depts = ['All', ...{for (final e in employees) e.department}];
        final filtered = _deptFilter == 'All' ? employees : employees.where((e) => e.department == _deptFilter).toList();

        return Column(children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              const Text('Department: ', style: TextStyle(fontWeight: FontWeight.w500)),
              const SizedBox(width: 8),
              Expanded(child: DropdownButton<String>(
                value: _deptFilter, isExpanded: true,
                items: depts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _deptFilter = v!),
              )),
            ]),
          ),
          Expanded(child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            itemCount: filtered.length,
            itemBuilder: (ctx, i) {
              final emp = filtered[i];
              final attendance = generateAttendance(emp.id);
              final today = attendance.lastOrNull;
              return Card(
                margin: const EdgeInsets.only(bottom: 4),
                child: ListTile(
                  dense: true,
                  leading: CircleAvatar(radius: 16, child: Text(emp.name[0])),
                  title: Text(emp.name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                  subtitle: Text(emp.department, style: const TextStyle(fontSize: 11)),
                  trailing: today != null ? StatusChip.fromStatus(today.statusLabel) : const StatusChip(label: 'N/A', color: Colors.grey),
                ),
              );
            },
          )),
        ]);
      },
    );
  }
}
