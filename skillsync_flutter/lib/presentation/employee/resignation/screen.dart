// lib/presentation/employee/resignation/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/resignation_request.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

class EmployeeResignationScreen extends ConsumerStatefulWidget {
  const EmployeeResignationScreen({super.key});
  @override ConsumerState<EmployeeResignationScreen> createState() => _State();
}

class _State extends ConsumerState<EmployeeResignationScreen> {
  List<ResignationRequest> _requests = [];
  bool _loading = true;
  DateTime _lastWorkingDate = DateTime.now().add(const Duration(days: 30));
  final _reasonCtrl = TextEditingController();
  bool _showForm = false;

  @override
  void initState() { super.initState(); _load(); }

  @override
  void dispose() { _reasonCtrl.dispose(); super.dispose(); }

  Future<void> _load() async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null) { setState(() => _loading = false); return; }
    final list = await ref.read(employeeRepositoryProvider).getResignations(employeeId: emp.id);
    if (mounted) setState(() { _requests = list.toList(); _loading = false; });
  }

  Future<void> _submit() async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null || _reasonCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill in all fields.')));
      return;
    }
    final notice = _lastWorkingDate.difference(DateTime.now()).inDays;
    final req = ResignationRequest(
      id: 'res_${DateTime.now().millisecondsSinceEpoch}',
      employeeId: emp.id, lastWorkingDate: _lastWorkingDate,
      noticePeriodDays: notice.clamp(0, 999), reason: _reasonCtrl.text.trim(),
      status: ResignationStatus.pending, submittedAt: DateTime.now(),
    );
    await ref.read(employeeRepositoryProvider).submitResignation(req);
    setState(() => _showForm = false);
    _reasonCtrl.clear();
    _load();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Resignation submitted. HR will review your request.'), backgroundColor: AppColors.warning));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();

    return ListView(padding: const EdgeInsets.all(16), children: [
      Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Row(children: [Icon(Icons.info_outline, color: AppColors.warning, size: 20), SizedBox(width: 8), Text('Resignation Notice', style: TextStyle(fontWeight: FontWeight.bold))]),
        const SizedBox(height: 8),
        const Text('Before submitting, please review your employment contract notice period requirements. Once submitted, this request will be reviewed by HR.', style: TextStyle(fontSize: 13, color: Colors.grey)),
      ]))),
      const SizedBox(height: 16),
      if (!_showForm)
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.riskHigh),
          onPressed: _requests.isEmpty ? () => setState(() => _showForm = true) : null,
          icon: const Icon(Icons.exit_to_app),
          label: const Text('Submit Resignation'),
        ),
      if (_showForm) ...[
        Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Resignation Form', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          const SizedBox(height: 12),
          ListTile(
            title: Text('Last Working Date: ${AppDateUtils.formatDate(_lastWorkingDate)}'),
            trailing: const Icon(Icons.calendar_today, size: 18),
            contentPadding: EdgeInsets.zero,
            onTap: () async {
              final d = await showDatePicker(context: context, initialDate: _lastWorkingDate, firstDate: DateTime.now().add(const Duration(days: 14)), lastDate: DateTime(2027));
              if (d != null) setState(() => _lastWorkingDate = d);
            },
          ),
          Row(children: [
            const Icon(Icons.schedule, size: 16, color: Colors.grey),
            const SizedBox(width: 4),
            Text('Notice period: ${_lastWorkingDate.difference(DateTime.now()).inDays} days', style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ]),
          const SizedBox(height: 12),
          TextField(controller: _reasonCtrl, decoration: const InputDecoration(labelText: 'Reason for resignation'), maxLines: 4),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: OutlinedButton(onPressed: () => setState(() => _showForm = false), child: const Text('Cancel'))),
            const SizedBox(width: 12),
            Expanded(child: ElevatedButton(style: ElevatedButton.styleFrom(backgroundColor: AppColors.riskHigh), onPressed: _submit, child: const Text('Submit'))),
          ]),
        ]))),
      ],
      if (_requests.isNotEmpty) ...[
        const SizedBox(height: 20),
        Text('Resignation History', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        ..._requests.map((r) => Card(margin: const EdgeInsets.only(bottom: 8), child: ListTile(
          leading: const Icon(Icons.exit_to_app),
          title: Text('Last day: ${AppDateUtils.formatDate(r.lastWorkingDate)}'),
          subtitle: Text('Notice: ${r.noticePeriodDays} days\n${r.reason}', maxLines: 2),
          isThreeLine: true,
          trailing: StatusChip.fromStatus(r.statusLabel),
        ))),
      ],
    ]);
  }
}
