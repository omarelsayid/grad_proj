// lib/presentation/hr/attendance/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../domain/entities/employee.dart';
import '../../../services/api_client.dart';
import '../../employee/dashboard/provider.dart';

// Fetches today's attendance for ALL employees from the backend in one call.
// Returns a map of { employeeId → status string }.
final _hrTodayAttendanceProvider = FutureProvider<Map<String, String>>((ref) async {
  final today = DateTime.now();
  final dateStr =
      '${today.year}-${today.month.toString().padLeft(2, '0')}-${today.day.toString().padLeft(2, '0')}';
  final records = await ApiClient.instance.getAttendance(from: dateStr, to: dateStr);
  return {
    for (final r in records)
      (r['employeeId'] as String): (r['status'] as String? ?? 'present'),
  };
});

class HrAttendanceScreen extends ConsumerStatefulWidget {
  const HrAttendanceScreen({super.key});
  @override
  ConsumerState<HrAttendanceScreen> createState() => _State();
}

class _State extends ConsumerState<HrAttendanceScreen> {
  String _deptFilter = 'All';

  @override
  Widget build(BuildContext context) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final attendanceAsync = ref.watch(_hrTodayAttendanceProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final employees = allEmps as List<Employee>;
        final depts = ['All', ...({for (final e in employees) e.department}.toList()..sort())];
        final filtered = _deptFilter == 'All'
            ? employees
            : employees.where((e) => e.department == _deptFilter).toList();

        return Column(children: [
          // Date + checked-in count header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
            child: Row(children: [
              const Icon(Icons.today_outlined, size: 14),
              const SizedBox(width: 6),
              Text(
                'Today · ${_formatDate(DateTime.now())}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
              ),
              const Spacer(),
              attendanceAsync.when(
                loading: () => const SizedBox(
                    width: 12, height: 12,
                    child: CircularProgressIndicator(strokeWidth: 2)),
                error: (_, __) => const Icon(Icons.cloud_off_outlined,
                    size: 14, color: Colors.orange),
                data: (map) => Text('${map.length} checked in',
                    style: const TextStyle(fontSize: 11, color: Colors.grey)),
              ),
            ]),
          ),
          // Department filter
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            child: Row(children: [
              const Text('Department: ',
                  style: TextStyle(fontWeight: FontWeight.w500)),
              const SizedBox(width: 8),
              Expanded(
                child: DropdownButton<String>(
                  value: _deptFilter,
                  isExpanded: true,
                  items: depts
                      .map((d) => DropdownMenuItem(
                          value: d,
                          child: Text(d, style: const TextStyle(fontSize: 13))))
                      .toList(),
                  onChanged: (v) => setState(() => _deptFilter = v!),
                ),
              ),
            ]),
          ),
          // Employee list
          Expanded(
            child: attendanceAsync.when(
              loading: () => const LoadingView(),
              // On error, still show employee list but without statuses
              error: (_, __) => _buildList(filtered, {}),
              data: (statusMap) => _buildList(filtered, statusMap),
            ),
          ),
        ]);
      },
    );
  }

  Widget _buildList(List<Employee> employees, Map<String, String> statusMap) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      itemCount: employees.length,
      itemBuilder: (ctx, i) {
        final emp = employees[i];
        final status = statusMap[emp.id];
        return Card(
          margin: const EdgeInsets.only(bottom: 4),
          child: ListTile(
            dense: true,
            leading: CircleAvatar(radius: 16, child: Text(emp.name[0])),
            title: Text(emp.name,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
            subtitle: Text(emp.department,
                style: const TextStyle(fontSize: 11)),
            trailing: status != null
                ? StatusChip.fromStatus(status)
                : const StatusChip(label: 'Not In', color: Colors.grey),
          ),
        );
      },
    );
  }

  String _formatDate(DateTime d) {
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${d.day} ${months[d.month]} ${d.year}';
  }
}
