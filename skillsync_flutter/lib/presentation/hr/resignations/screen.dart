// lib/presentation/hr/resignations/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/resignation_request.dart';
import '../../../domain/entities/employee.dart';
import '../../auth/auth_provider.dart';

class HrResignationsScreen extends ConsumerStatefulWidget {
  const HrResignationsScreen({super.key});
  @override ConsumerState<HrResignationsScreen> createState() => _State();
}

class _State extends ConsumerState<HrResignationsScreen> {
  List<ResignationRequest> _requests = [];
  Map<String, Employee> _empMap = {};
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final repo = ref.read(employeeRepositoryProvider);
    final emps = await repo.getAll();
    final requests = await repo.getResignations();
    if (mounted) setState(() {
      _empMap = {for (final e in emps) e.id: e};
      _requests = requests.toList();
      _loading = false;
    });
  }

  Future<void> _updateStatus(ResignationRequest req, ResignationStatus status) async {
    await ref.read(employeeRepositoryProvider).updateResignationStatus(req.id, status);
    setState(() {
      final i = _requests.indexWhere((r) => r.id == req.id);
      if (i != -1) _requests[i] = req.copyWith(status: status);
    });
    final msg = status == ResignationStatus.approved ? 'Resignation approved.' : 'Resignation rejected.';
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();

    if (_requests.isEmpty) {
      return const EmptyState(icon: Icons.exit_to_app_outlined, title: 'No resignation requests');
    }

    return ListView(padding: const EdgeInsets.all(16), children: [
      Text('${_requests.length} Resignation${_requests.length != 1 ? 's' : ''}',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      ..._requests.map((r) {
        final emp = _empMap[r.employeeId];
        final isPending = r.status == ResignationStatus.pending;
        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                CircleAvatar(child: Text(emp?.name[0] ?? '?')),
                const SizedBox(width: 10),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(emp?.name ?? 'Unknown', style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text(emp?.currentRole ?? '', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ])),
                StatusChip.fromStatus(r.statusLabel),
              ]),
              const SizedBox(height: 10),
              Row(children: [
                const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                const SizedBox(width: 4),
                Text('Last day: ${AppDateUtils.formatDate(r.lastWorkingDate)}', style: const TextStyle(fontSize: 13)),
              ]),
              Row(children: [
                const Icon(Icons.schedule, size: 14, color: Colors.grey),
                const SizedBox(width: 4),
                Text('Notice: ${r.noticePeriodDays} days', style: const TextStyle(fontSize: 12, color: Colors.grey)),
              ]),
              if (r.reason.isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(r.reason, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              ],
              if (isPending) ...[
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(child: OutlinedButton(onPressed: () => _updateStatus(r, ResignationStatus.rejected), child: const Text('Reject'), style: OutlinedButton.styleFrom(foregroundColor: AppColors.riskHigh))),
                  const SizedBox(width: 8),
                  Expanded(child: ElevatedButton(onPressed: () => _updateStatus(r, ResignationStatus.approved), child: const Text('Approve'), style: ElevatedButton.styleFrom(backgroundColor: AppColors.success))),
                ]),
              ],
            ]),
          ),
        );
      }),
    ]);
  }
}
