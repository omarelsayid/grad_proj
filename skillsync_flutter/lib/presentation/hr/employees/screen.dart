// lib/presentation/hr/employees/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/employee_skill.dart';
import '../../auth/auth_provider.dart';
import '../../employee/dashboard/provider.dart';

class HrEmployeesScreen extends ConsumerStatefulWidget {
  const HrEmployeesScreen({super.key});
  @override ConsumerState<HrEmployeesScreen> createState() => _State();
}

class _State extends ConsumerState<HrEmployeesScreen> {
  String _searchQuery = '';
  String _deptFilter = 'All';

  @override
  Widget build(BuildContext context) {
    final empsAsync = ref.watch(allEmployeesProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) {
        final depts = ['All', ...{for (final e in allEmps as List<Employee>) e.department}];
        final filtered = allEmps.where((e) {
          final matchSearch = _searchQuery.isEmpty || e.name.toLowerCase().contains(_searchQuery.toLowerCase()) || e.email.toLowerCase().contains(_searchQuery.toLowerCase());
          final matchDept = _deptFilter == 'All' || e.department == _deptFilter;
          return matchSearch && matchDept;
        }).toList();

        return Column(children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              Expanded(child: TextField(
                decoration: const InputDecoration(hintText: 'Search employees...', prefixIcon: Icon(Icons.search), isDense: true),
                onChanged: (v) => setState(() => _searchQuery = v),
              )),
              const SizedBox(width: 8),
              DropdownButton<String>(
                value: _deptFilter,
                items: depts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 12)))).toList(),
                onChanged: (v) => setState(() => _deptFilter = v!),
              ),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('${filtered.length} employees', style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ElevatedButton.icon(
                onPressed: () => _showAddDialog(context),
                icon: const Icon(Icons.person_add, size: 16),
                label: const Text('Add'),
              ),
            ]),
          ),
          Expanded(
            child: filtered.isEmpty
                ? const EmptyState(icon: Icons.people_outline, title: 'No employees found')
                : ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: filtered.length,
                    itemBuilder: (ctx, i) => _EmpCard(employee: filtered[i]),
                  ),
          ),
        ]);
      },
    );
  }

  void _showAddDialog(BuildContext context) {
    final nameCtrl = TextEditingController();
    final emailCtrl = TextEditingController();
    final deptCtrl = TextEditingController();
    showDialog(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Add Employee'),
      content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Full Name')),
        const SizedBox(height: 8),
        TextField(controller: emailCtrl, decoration: const InputDecoration(labelText: 'Email')),
        const SizedBox(height: 8),
        TextField(controller: deptCtrl, decoration: const InputDecoration(labelText: 'Department')),
      ])),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
        ElevatedButton(onPressed: () async {
          final emp = Employee(
            id: 'emp_new_${DateTime.now().millisecondsSinceEpoch}',
            name: nameCtrl.text.trim(), email: emailCtrl.text.trim(),
            avatarUrl: '', currentRole: 'Junior Software Engineer',
            roleId: 'r01', department: deptCtrl.text.trim(),
            joinDate: DateTime.now(), salary: 10000, phone: '',
            skills: const [], commuteDistance: 'near', satisfactionScore: 75,
          );
          await ref.read(employeeRepositoryProvider).add(emp);
          ref.invalidate(allEmployeesProvider);
          if (ctx.mounted) Navigator.pop(ctx);
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Employee added successfully.')));
        }, child: const Text('Add')),
      ],
    ));
  }
}

class _EmpCard extends StatelessWidget {
  final Employee employee;
  const _EmpCard({required this.employee});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 6),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppColors.primary.withOpacity(0.12),
          child: Text(employee.name[0], style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
        ),
        title: Text(employee.name, style: const TextStyle(fontWeight: FontWeight.w500)),
        subtitle: Text('${employee.currentRole} • ${employee.department}', style: const TextStyle(fontSize: 12)),
        trailing: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text('${employee.skills.length} skills', style: const TextStyle(fontSize: 11, color: Colors.grey)),
          Text('${employee.tenureYears.toStringAsFixed(1)}y', style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ]),
      ),
    );
  }
}
