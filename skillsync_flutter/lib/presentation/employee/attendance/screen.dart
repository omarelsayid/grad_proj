// lib/presentation/employee/attendance/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/attendance_record.dart';
import '../../../services/api_client.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _attendanceProvider = FutureProvider<List<AttendanceRecord>>((ref) async {
  final emp = ref.read(authProvider).currentUser;
  if (emp == null) return [];
  final repo = ref.read(employeeRepositoryProvider);
  return repo.getAttendance(emp.id);
});

// Tracks today's record so the button can update without a full page refresh
final _todayProvider = FutureProvider<AttendanceRecord?>((ref) async {
  final records = await ref.watch(_attendanceProvider.future);
  final today = DateTime.now();
  try {
    return records.firstWhere((r) =>
        r.date.year == today.year &&
        r.date.month == today.month &&
        r.date.day == today.day);
  } catch (_) {
    return null;
  }
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
        final summary = _buildSummary(records);
        return Column(
          children: [
            _CheckInBanner(onDone: () => ref.invalidate(_attendanceProvider)),
            _SummaryRow(summary: summary),
            Expanded(
              child: records.isEmpty
                  ? const EmptyState(icon: Icons.calendar_month_outlined, title: 'No attendance records')
                  : ListView.builder(
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

class _CheckInBanner extends ConsumerStatefulWidget {
  final VoidCallback onDone;
  const _CheckInBanner({required this.onDone});

  @override
  ConsumerState<_CheckInBanner> createState() => _CheckInBannerState();
}

class _CheckInBannerState extends ConsumerState<_CheckInBanner> {
  bool _loading = false;

  Future<void> _tap(bool isCheckIn) async {
    setState(() => _loading = true);
    try {
      if (isCheckIn) {
        await ApiClient.instance.checkIn();
      } else {
        await ApiClient.instance.checkOut();
      }
      widget.onDone();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final todayAsync = ref.watch(_todayProvider);
    final now = DateTime.now();
    final timeStr =
        '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
    final dateStr =
        '${now.day} ${_monthName(now.month)} ${now.year}';

    return todayAsync.when(
      loading: () => const SizedBox(height: 72),
      error: (_, __) => const SizedBox.shrink(),
      data: (today) {
        final checkedIn  = today?.checkIn != null;
        final checkedOut = today?.checkOut != null;

        return Container(
          margin: const EdgeInsets.all(16),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: checkedOut
                  ? [const Color(0xFF065f46), const Color(0xFF059669)]
                  : checkedIn
                      ? [const Color(0xFF1e3a5f), const Color(0xFF0369a1)]
                      : [const Color(0xFF1e3a5f), const Color(0xFF334155)],
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(children: [
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(timeStr,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1)),
              Text(dateStr,
                  style: const TextStyle(color: Colors.white70, fontSize: 12)),
              if (checkedIn && !checkedOut)
                Text('Checked in at ${today!.checkIn != null ? AppDateUtils.formatTime(today.checkIn!) : "—"}',
                    style: const TextStyle(color: Colors.white60, fontSize: 11)),
              if (checkedOut)
                const Text('Done for today ✓',
                    style: TextStyle(color: Colors.white60, fontSize: 11)),
            ]),
            const Spacer(),
            if (_loading)
              const SizedBox(
                  width: 36,
                  height: 36,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white))
            else if (checkedOut)
              const Icon(Icons.check_circle_outline,
                  color: Colors.white60, size: 32)
            else
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: checkedIn ? AppColors.success : AppColors.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
                onPressed: () => _tap(!checkedIn),
                icon: Icon(checkedIn ? Icons.logout : Icons.login, size: 18),
                label: Text(checkedIn ? 'Check Out' : 'Check In'),
              ),
          ]),
        );
      },
    );
  }

  String _monthName(int m) => const [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
      ][m];
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
            ? Text(
                '${AppDateUtils.formatTime(record.checkIn!)} — ${record.checkOut != null ? AppDateUtils.formatTime(record.checkOut!) : 'ongoing'}',
                style: const TextStyle(fontSize: 12))
            : null,
        trailing: record.hoursWorked != null
            ? Text('${record.hoursWorked!.inHours}h',
                style: const TextStyle(fontSize: 12, color: Colors.grey))
            : null,
      ),
    );
  }
}
