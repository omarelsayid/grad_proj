// lib/presentation/hr/payroll/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/payroll_record.dart';
import '../../../data/mock/mock_static_data.dart';
import '../../employee/dashboard/provider.dart';

class HrPayrollScreen extends ConsumerStatefulWidget {
  const HrPayrollScreen({super.key});
  @override ConsumerState<HrPayrollScreen> createState() => _State();
}

class _State extends ConsumerState<HrPayrollScreen> {
  int _month = 4, _year = 2026;
  String _statusFilter = 'All';
  final _egp = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

  @override
  Widget build(BuildContext context) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final employees = allEmps as List<Employee>;
        final records = employees.map((emp) {
          final all = getPayrollForEmployee(emp.id, emp.salary);
          return all.firstWhere((r) => r.month == _month && r.year == _year, orElse: () => all.first);
        }).where((r) => _statusFilter == 'All' || r.statusLabel == _statusFilter).toList();

        final totalNet = records.fold(0.0, (sum, r) => sum + r.netSalary);

        return Column(children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              Expanded(child: DropdownButton<int>(
                value: _month, isExpanded: true,
                items: List.generate(12, (i) => DropdownMenuItem(value: i + 1, child: Text(DateFormat('MMMM').format(DateTime(2026, i + 1)), style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _month = v!),
              )),
              const SizedBox(width: 8),
              Expanded(child: DropdownButton<String>(
                value: _statusFilter, isExpanded: true,
                items: ['All', 'Pending', 'Processed', 'Paid'].map((s) => DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _statusFilter = v!),
              )),
            ]),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('${records.length} employees', style: const TextStyle(fontWeight: FontWeight.w500)),
              Text('Total: ${_egp.format(totalNet)}', style: const TextStyle(fontWeight: FontWeight.bold)),
            ]),
          ),
          Expanded(child: ListView.builder(
            itemCount: records.length,
            itemBuilder: (ctx, i) {
              final record = records[i];
              final emp = employees.firstWhere((e) => e.id == record.employeeId, orElse: () => employees.first);
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.grey.withOpacity(0.1)))),
                child: Row(children: [
                  Expanded(flex: 3, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(emp.name, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                    Text(emp.department, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                  ])),
                  Expanded(flex: 2, child: Text(_egp.format(record.netSalary), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500))),
                  StatusChip.fromStatus(record.statusLabel),
                ]),
              );
            },
          )),
        ]);
      },
    );
  }
}
