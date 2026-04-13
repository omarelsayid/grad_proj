// lib/presentation/employee/payroll/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/payroll_record.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _payrollProvider = FutureProvider<List<PayrollRecord>>((ref) async {
  final emp = ref.read(authProvider).currentUser;
  if (emp == null) return [];
  return ref.read(employeeRepositoryProvider).getPayroll(employeeId: emp.id);
});

class EmployeePayrollScreen extends ConsumerStatefulWidget {
  const EmployeePayrollScreen({super.key});
  @override ConsumerState<EmployeePayrollScreen> createState() => _State();
}

class _State extends ConsumerState<EmployeePayrollScreen> {
  int _selectedIdx = 0;
  final _egp = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

  @override
  Widget build(BuildContext context) {
    final payrollAsync = ref.watch(_payrollProvider);

    return payrollAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (records) {
        if (records.isEmpty) {
          return const Center(child: Text('No payroll records found.'));
        }

        final current = records[_selectedIdx];
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildMonthSelector(records),
              const SizedBox(height: 20),
              _buildPayslip(context, current),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMonthSelector(List<PayrollRecord> records) {
    return SizedBox(
      height: 40,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        itemCount: records.length,
        itemBuilder: (ctx, i) {
          final r = records[i];
          final label = DateFormat('MMM yy').format(DateTime(r.year, r.month));
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(label),
              selected: _selectedIdx == i,
              onSelected: (_) => setState(() => _selectedIdx = i),
            ),
          );
        },
      ),
    );
  }

  Widget _buildPayslip(BuildContext context, PayrollRecord record) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text(DateFormat('MMMM yyyy').format(DateTime(record.year, record.month)),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
              StatusChip.fromStatus(record.statusLabel),
            ]),
            const Divider(height: 24),
            _Row('Basic Salary', record.basicSalary),
            _Row('Allowances', record.allowances, positive: true),
            _Row('Deductions', record.deductions, positive: false),
            const Divider(height: 24),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              const Text('Net Salary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Text(_egp.format(record.netSalary), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: AppColors.success)),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _Row(String label, double amount, {bool? positive}) {
    final _egpLocal = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);
    final color = positive == true ? AppColors.success : positive == false ? AppColors.riskHigh : null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label),
        Text(
          '${positive == false ? '-' : ''}${_egpLocal.format(amount)}',
          style: TextStyle(fontWeight: FontWeight.w500, color: color),
        ),
      ]),
    );
  }
}
