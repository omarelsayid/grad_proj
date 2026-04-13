// lib/presentation/manager/leaves/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/leave_request.dart';
import '../../../domain/entities/employee.dart';
import '../../auth/auth_provider.dart';

class ManagerLeavesScreen extends ConsumerStatefulWidget {
  const ManagerLeavesScreen({super.key});
  @override ConsumerState<ManagerLeavesScreen> createState() => _State();
}

class _State extends ConsumerState<ManagerLeavesScreen> {
  List<LeaveRequest> _requests = [];
  Map<String, Employee> _empMap = {};
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final repo = ref.read(employeeRepositoryProvider);
    final emps = await repo.getAll();
    final requests = await repo.getLeaveRequests();
    if (mounted) setState(() {
      _empMap = {for (final e in emps) e.id: e};
      _requests = requests.toList();
      _loading = false;
    });
  }

  Future<void> _updateStatus(LeaveRequest req, LeaveStatus status) async {
    await ref.read(employeeRepositoryProvider).updateLeaveStatus(req.id, status);
    setState(() {
      final i = _requests.indexWhere((r) => r.id == req.id);
      if (i != -1) _requests[i] = req.copyWith(status: status);
    });
    final msg = status == LeaveStatus.approved ? 'Leave approved.' : 'Leave rejected.';
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();

    final pending = _requests.where((r) => r.status == LeaveStatus.pending).toList();
    final others = _requests.where((r) => r.status != LeaveStatus.pending).toList();

    return ListView(padding: const EdgeInsets.all(16), children: [
      Text('Pending Approval (${pending.length})', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 8),
      if (pending.isEmpty) const EmptyState(icon: Icons.check_circle_outline, title: 'No pending requests'),
      ...pending.map((r) => _LeaveCard(request: r, employee: _empMap[r.employeeId], onApprove: () => _updateStatus(r, LeaveStatus.approved), onReject: () => _updateStatus(r, LeaveStatus.rejected))),
      if (others.isNotEmpty) ...[
        const SizedBox(height: 20),
        Text('Processed (${others.length})', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ...others.map((r) => _LeaveCard(request: r, employee: _empMap[r.employeeId])),
      ],
    ]);
  }
}

class _LeaveCard extends StatelessWidget {
  final LeaveRequest request;
  final Employee? employee;
  final VoidCallback? onApprove, onReject;
  const _LeaveCard({required this.request, this.employee, this.onApprove, this.onReject});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            CircleAvatar(child: Text(employee?.name[0] ?? '?')),
            const SizedBox(width: 10),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(employee?.name ?? 'Unknown', style: const TextStyle(fontWeight: FontWeight.bold)),
              Text('${request.leaveType.toUpperCase()} — ${request.durationDays} days', style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ])),
            StatusChip.fromStatus(request.statusLabel),
          ]),
          const SizedBox(height: 8),
          Text('${AppDateUtils.formatDate(request.startDate)} → ${AppDateUtils.formatDate(request.endDate)}', style: const TextStyle(fontSize: 13)),
          if (request.reason.isNotEmpty) Text(request.reason, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          if (onApprove != null && onReject != null) ...[
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: OutlinedButton.icon(onPressed: onReject, icon: const Icon(Icons.close, size: 16), label: const Text('Reject'), style: OutlinedButton.styleFrom(foregroundColor: AppColors.riskHigh))),
              const SizedBox(width: 8),
              Expanded(child: ElevatedButton.icon(onPressed: onApprove, icon: const Icon(Icons.check, size: 16), label: const Text('Approve'), style: ElevatedButton.styleFrom(backgroundColor: AppColors.success))),
            ]),
          ],
        ]),
      ),
    );
  }
}
