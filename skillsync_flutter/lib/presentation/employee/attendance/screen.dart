// lib/presentation/employee/attendance/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/attendance_record.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _attendanceProvider = FutureProvider<List<AttendanceRecord>>((ref) async {
  final emp = ref.read(authProvider).currentUser;
  if (emp == null) return [];
  final repo = ref.read(employeeRepositoryProvider);
  return repo.getAttendance(emp.id);
});

class EmployeeAttendanceScreen extends ConsumerWidget {
  const EmployeeAttendanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final attendanceAsync = ref.watch(_attendanceProvider);

    return attendanceAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (records) {
        if (records.isEmpty) {
          return const EmptyState(icon: Icons.calendar_month_outlined, title: 'No attendance records');
        }

        final summary = _buildSummary(records);
        return Column(
          children: [
            _SummaryRow(summary: summary),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: records.length,
                itemBuilder: (ctx, i) => _AttendanceRow(record: records[i]),
              ),
            ),
          ],
        );
      },
    );
  }

  Map<String, int> _buildSummary(List<AttendanceRecord> records) {
    final counts = <String, int>{};
    for (final r in records) {
      counts[r.statusLabel] = (counts[r.statusLabel] ?? 0) + 1;
    }
    return counts;
  }
}

class _SummaryRow extends StatelessWidget {
  final Map<String, int> summary;
  const _SummaryRow({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha: 0.5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: summary.entries.map((e) => Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(e.key, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        )).toList(),
      ),
    );
  }
}

class _AttendanceRow extends StatelessWidget {
  final AttendanceRecord record;
  const _AttendanceRow({required this.record});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 6),
      child: ListTile(
        dense: true,
        leading: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(AppDateUtils.formatDate(record.date).split(' ')[0],
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            Text(AppDateUtils.formatDate(record.date).split(' ')[1],
                style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        title: StatusChip.fromStatus(record.statusLabel),
        subtitle: record.checkIn != null
            ? Text('${AppDateUtils.formatTime(record.checkIn!)} — ${record.checkOut != null ? AppDateUtils.formatTime(record.checkOut!) : 'ongoing'}',
                style: const TextStyle(fontSize: 12))
            : null,
        trailing: record.hoursWorked != null
            ? Text('${record.hoursWorked!.inHours}h', style: const TextStyle(fontSize: 12, color: Colors.grey))
            : null,
      ),
    );
  }
}
