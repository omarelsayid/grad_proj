// lib/presentation/manager/attendance/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/attendance_record.dart';
import '../../../data/mock/mock_attendance.dart';
import '../../employee/dashboard/provider.dart';

class ManagerAttendanceScreen extends ConsumerWidget {
  const ManagerAttendanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final teamEmps = (allEmps as List<Employee>).take(10).toList();
        final today = DateTime(2026, 3, 15);
        final records = <(Employee, AttendanceRecord?)>[];
        for (final emp in teamEmps) {
          final attendance = generateAttendance(emp.id);
          final todayRecord = attendance.where((a) => a.date.day == today.day && a.date.month == today.month).firstOrNull;
          records.add((emp, todayRecord));
        }

        final summary = <String, int>{};
        for (final (_, r) in records) {
          final label = r?.statusLabel ?? 'Absent';
          summary[label] = (summary[label] ?? 0) + 1;
        }

        return Column(
          children: [
            _SummaryBar(summary: summary),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: records.length,
                itemBuilder: (ctx, i) {
                  final (emp, record) = records[i];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 6),
                    child: ListTile(
                      leading: CircleAvatar(child: Text(emp.name[0])),
                      title: Text(emp.name),
                      subtitle: Text(emp.currentRole, style: const TextStyle(fontSize: 12)),
                      trailing: record != null
                          ? StatusChip.fromStatus(record.statusLabel)
                          : const StatusChip(label: 'N/A', color: Colors.grey),
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
    );
  }
}

class _SummaryBar extends StatelessWidget {
  final Map<String, int> summary;
  const _SummaryBar({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: summary.entries.map((e) => Column(mainAxisSize: MainAxisSize.min, children: [
          Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          Text(e.key, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ])).toList(),
      ),
    );
  }
}
