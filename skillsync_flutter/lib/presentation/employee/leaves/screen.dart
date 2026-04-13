// lib/presentation/employee/leaves/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/leave_balance.dart';
import '../../../domain/entities/leave_request.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _empLeaveBalanceProvider = FutureProvider<LeaveBalance>((ref) async {
  final emp = ref.read(authProvider).currentUser;
  if (emp == null) throw Exception('Not authenticated');
  return ref.read(employeeRepositoryProvider).getLeaveBalance(emp.id);
});

final _leaveRequestsProvider = StateProvider<List<LeaveRequest>>((ref) {
  return [];
});

class EmployeeLeavesScreen extends ConsumerStatefulWidget {
  const EmployeeLeavesScreen({super.key});
  @override ConsumerState<EmployeeLeavesScreen> createState() => _State();
}

class _State extends ConsumerState<EmployeeLeavesScreen> {
  List<LeaveRequest> _requests = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null) return;
    final repo = ref.read(employeeRepositoryProvider);
    final requests = await repo.getLeaveRequests(employeeId: emp.id);
    if (mounted) setState(() => _requests = requests);
  }

  Future<void> _submit(String type, DateTime start, DateTime end, String reason) async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null) return;
    final req = LeaveRequest(
      id: 'lr_${DateTime.now().millisecondsSinceEpoch}',
      employeeId: emp.id,
      leaveType: type,
      startDate: start,
      endDate: end,
      reason: reason,
      status: LeaveStatus.pending,
    );
    await ref.read(employeeRepositoryProvider).submitLeaveRequest(req);
    await _load();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Leave request submitted successfully.')));
  }

  @override
  Widget build(BuildContext context) {
    final balanceAsync = ref.watch(_empLeaveBalanceProvider);
    return balanceAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (balance) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _BalanceCards(balance: balance),
          const SizedBox(height: 20),
          _RequestForm(onSubmit: _submit),
          const SizedBox(height: 20),
          Text('Leave History', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          if (_requests.isEmpty)
            const Center(child: Padding(padding: EdgeInsets.all(16), child: Text('No leave requests yet.')))
          else
            ..._requests.map((r) => _LeaveCard(request: r)),
        ],
      ),
    );
  }
}

class _BalanceCards extends StatelessWidget {
  final LeaveBalance balance;
  const _BalanceCards({required this.balance});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Expanded(child: _BalanceTile(type: 'Annual', used: balance.annualUsed, total: balance.annualTotal, color: AppColors.primary)),
      const SizedBox(width: 8),
      Expanded(child: _BalanceTile(type: 'Sick', used: balance.sickUsed, total: balance.sickTotal, color: AppColors.secondary)),
      const SizedBox(width: 8),
      Expanded(child: _BalanceTile(type: 'Compassionate', used: balance.compassionateUsed, total: balance.compassionateTotal, color: AppColors.warning)),
    ]);
  }
}

class _BalanceTile extends StatelessWidget {
  final String type;
  final int used, total;
  final Color color;
  const _BalanceTile({required this.type, required this.used, required this.total, required this.color});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(children: [
          Text('${total - used}', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
          Text('left', style: const TextStyle(fontSize: 11, color: Colors.grey)),
          const SizedBox(height: 4),
          Text(type, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
          Text('$used/$total used', style: const TextStyle(fontSize: 10, color: Colors.grey)),
        ]),
      ),
    );
  }
}

class _RequestForm extends StatefulWidget {
  final Future<void> Function(String, DateTime, DateTime, String) onSubmit;
  const _RequestForm({required this.onSubmit});
  @override State<_RequestForm> createState() => _RequestFormState();
}

class _RequestFormState extends State<_RequestForm> {
  String _type = 'annual';
  DateTime _start = DateTime.now().add(const Duration(days: 3));
  DateTime _end = DateTime.now().add(const Duration(days: 5));
  final _reasonCtrl = TextEditingController();
  bool _expanded = false;

  @override
  void dispose() { _reasonCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          GestureDetector(
            onTap: () => setState(() => _expanded = !_expanded),
            child: Row(children: [
              const Icon(Icons.add_circle_outline, color: AppColors.primary),
              const SizedBox(width: 8),
              const Text('Request Leave', style: TextStyle(fontWeight: FontWeight.bold)),
              const Spacer(),
              Icon(_expanded ? Icons.expand_less : Icons.expand_more),
            ]),
          ),
          if (_expanded) ...[
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(labelText: 'Leave Type'),
              items: const [
                DropdownMenuItem(value: 'annual', child: Text('Annual')),
                DropdownMenuItem(value: 'sick', child: Text('Sick')),
                DropdownMenuItem(value: 'compassionate', child: Text('Compassionate')),
              ],
              onChanged: (v) => setState(() => _type = v!),
            ),
            const SizedBox(height: 8),
            Row(children: [
              Expanded(child: ListTile(
                title: Text('Start: ${AppDateUtils.formatShort(_start)}'),
                trailing: const Icon(Icons.calendar_today, size: 18),
                onTap: () async {
                  final d = await showDatePicker(context: context, initialDate: _start, firstDate: DateTime.now(), lastDate: DateTime(2027));
                  if (d != null) setState(() => _start = d);
                },
              )),
              Expanded(child: ListTile(
                title: Text('End: ${AppDateUtils.formatShort(_end)}'),
                trailing: const Icon(Icons.calendar_today, size: 18),
                onTap: () async {
                  final d = await showDatePicker(context: context, initialDate: _end, firstDate: _start, lastDate: DateTime(2027));
                  if (d != null) setState(() => _end = d);
                },
              )),
            ]),
            TextField(controller: _reasonCtrl, decoration: const InputDecoration(labelText: 'Reason'), maxLines: 2),
            const SizedBox(height: 12),
            SizedBox(width: double.infinity, child: ElevatedButton(
              onPressed: () {
                widget.onSubmit(_type, _start, _end, _reasonCtrl.text);
                setState(() => _expanded = false);
              },
              child: const Text('Submit Request'),
            )),
          ],
        ]),
      ),
    );
  }
}

class _LeaveCard extends StatelessWidget {
  final LeaveRequest request;
  const _LeaveCard({required this.request});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: const Icon(Icons.beach_access_outlined),
        title: Text('${request.leaveType.toUpperCase()} — ${request.durationDays} days'),
        subtitle: Text('${AppDateUtils.formatDate(request.startDate)} → ${AppDateUtils.formatDate(request.endDate)}\n${request.reason}'),
        isThreeLine: true,
        trailing: StatusChip.fromStatus(request.statusLabel),
      ),
    );
  }
}
