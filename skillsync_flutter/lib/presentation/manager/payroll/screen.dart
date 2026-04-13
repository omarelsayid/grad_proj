// lib/presentation/manager/payroll/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/status_chip.dart';
import '../../../domain/entities/employee.dart';
import '../../../data/mock/mock_static_data.dart';
import '../../employee/dashboard/provider.dart';

class ManagerPayrollScreen extends ConsumerWidget {
  const ManagerPayrollScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final egp = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final teamEmps = (allEmps as List<Employee>).take(10).toList();
        final payrollData = teamEmps.map((emp) {
          final records = getPayrollForEmployee(emp.id, emp.salary);
          final latest = records.isNotEmpty ? records.first : null;
          return (employee: emp, record: latest);
        }).toList();

        return Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.4),
              child: Row(children: [
                const Expanded(flex: 3, child: Text('Employee', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                const Expanded(flex: 2, child: Text('Net Salary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                const Expanded(child: Text('Status', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
              ]),
            ),
            Expanded(
              child: ListView.builder(
                itemCount: payrollData.length,
                itemBuilder: (ctx, i) {
                  final item = payrollData[i];
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      border: Border(bottom: BorderSide(color: Colors.grey.withOpacity(0.1))),
                    ),
                    child: Row(children: [
                      Expanded(flex: 3, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(item.employee.name, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                        Text(item.employee.currentRole, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                      ])),
                      Expanded(flex: 2, child: Text(
                        item.record != null ? egp.format(item.record!.netSalary) : '-',
                        style: const TextStyle(fontWeight: FontWeight.w500),
                      )),
                      Expanded(child: item.record != null
                          ? StatusChip.fromStatus(item.record!.statusLabel)
                          : const StatusChip(label: 'N/A', color: Colors.grey)),
                    ]),
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
