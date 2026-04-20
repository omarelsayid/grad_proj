// lib/presentation/manager/learning/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/learning_item.dart';
import '../../../domain/entities/learning_progress.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/get_suggested_learning_use_case.dart';
import '../../employee/dashboard/provider.dart';
import '../../employee/learning/screen.dart';

const _roleFitUc = CalculateRoleFitUseCase();
const _learningUc = GetSuggestedLearningUseCase(_roleFitUc);

// Deterministic mock progress so every manager sees the same snapshot
LearningStatus _mockStatus(String empId, String itemId) {
  final hash = (empId.hashCode ^ itemId.hashCode).abs() % 5;
  if (hash <= 1) return LearningStatus.completed;
  if (hash == 2) return LearningStatus.inProgress;
  return LearningStatus.notStarted;
}

class ManagerTeamLearningScreen extends ConsumerWidget {
  const ManagerTeamLearningScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);
    final learningAsync = ref.watch(learningItemsProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) => learningAsync.when(
          loading: () => const LoadingView(),
          error: (e, _) => Center(child: Text('$e')),
          data: (allItems) {
            final teamEmps = allEmps.take(10).toList();
            final roleMap = {for (final r in roles) r.id: r};

            int totalCompleted = 0;
            int totalInProgress = 0;
            int totalItems = 0;

            final empData = teamEmps.map((emp) {
              final role = roleMap[emp.roleId];
              final items = (role != null
                      ? _learningUc.call(
                          employee: emp, targetRole: role, catalog: allItems)
                      : allItems)
                  .take(5)
                  .toList();
              final progress = {
                for (final item in items) item.id: _mockStatus(emp.id, item.id)
              };
              final done =
                  progress.values.where((s) => s == LearningStatus.completed).length;
              final wip =
                  progress.values.where((s) => s == LearningStatus.inProgress).length;
              totalCompleted += done;
              totalInProgress += wip;
              totalItems += items.length;
              return (emp: emp, items: items, progress: progress, done: done);
            }).toList();

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _TeamSummary(
                    total: totalItems,
                    completed: totalCompleted,
                    inProgress: totalInProgress,
                  ),
                  const SizedBox(height: 20),
                  Text('Team Members',
                      style: Theme.of(context)
                          .textTheme
                          .titleMedium
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  ...empData.map((d) => _EmployeeLearningCard(
                        employee: d.emp,
                        items: d.items,
                        progress: d.progress,
                        completed: d.done,
                      )),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

// ── Team summary card ──────────────────────────────────────────────────────────
class _TeamSummary extends StatelessWidget {
  final int total;
  final int completed;
  final int inProgress;

  const _TeamSummary(
      {required this.total,
      required this.completed,
      required this.inProgress});

  @override
  Widget build(BuildContext context) {
    final pct = total > 0 ? completed / total : 0.0;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Team Overview',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 14),
          Row(children: [
            _Pill('$completed', 'Completed', AppColors.success),
            const SizedBox(width: 10),
            _Pill('$inProgress', 'In Progress', AppColors.warning),
            const SizedBox(width: 10),
            _Pill('${total - completed - inProgress}', 'Not Started',
                Colors.grey),
          ]),
          const SizedBox(height: 14),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct,
              backgroundColor: Colors.grey.shade200,
              color: AppColors.success,
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 6),
          Text('${(pct * 100).toInt()}% of assigned courses completed',
              style: const TextStyle(fontSize: 12, color: Colors.grey)),
        ]),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String value;
  final String label;
  final Color color;

  const _Pill(this.value, this.label, this.color);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(children: [
          Text(value,
              style: TextStyle(
                  fontWeight: FontWeight.bold, fontSize: 20, color: color)),
          const SizedBox(height: 2),
          Text(label,
              style: const TextStyle(fontSize: 10, color: Colors.grey)),
        ]),
      ),
    );
  }
}

// ── Employee learning card ─────────────────────────────────────────────────────
class _EmployeeLearningCard extends StatelessWidget {
  final Employee employee;
  final List<LearningItem> items;
  final Map<String, LearningStatus> progress;
  final int completed;

  const _EmployeeLearningCard({
    required this.employee,
    required this.items,
    required this.progress,
    required this.completed,
  });

  @override
  Widget build(BuildContext context) {
    final pct = items.isNotEmpty ? completed / items.length : 0.0;
    final barColor = pct >= 0.7 ? AppColors.success : AppColors.warning;
    final initials = employee.name
        .split(' ')
        .map((n) => n.isNotEmpty ? n[0] : '')
        .take(2)
        .join();

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                child: Text(initials,
                    style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary)),
              ),
              const SizedBox(width: 10),
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(employee.name,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 14)),
                    Text(employee.department,
                        style: const TextStyle(
                            fontSize: 11, color: Colors.grey)),
                  ])),
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text('$completed/${items.length}',
                    style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: barColor,
                        fontSize: 14)),
                const Text('courses', style: TextStyle(fontSize: 10, color: Colors.grey)),
              ]),
            ]),
            const SizedBox(height: 10),
            // Progress bar
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: pct,
                backgroundColor: Colors.grey.shade200,
                color: barColor,
                minHeight: 5,
              ),
            ),
            const SizedBox(height: 12),
            // Course list (top 3)
            ...items.take(3).map((item) {
              final status = progress[item.id] ?? LearningStatus.notStarted;
              final (color, icon) = switch (status) {
                LearningStatus.notStarted =>
                  (Colors.grey, Icons.radio_button_unchecked),
                LearningStatus.inProgress =>
                  (AppColors.warning, Icons.pending_outlined),
                LearningStatus.completed =>
                  (AppColors.success, Icons.check_circle_outline),
              };
              return Padding(
                padding: const EdgeInsets.only(top: 5),
                child: Row(children: [
                  Icon(icon, size: 14, color: color),
                  const SizedBox(width: 8),
                  Expanded(
                      child: Text(item.title,
                          style: const TextStyle(fontSize: 12),
                          overflow: TextOverflow.ellipsis)),
                  const SizedBox(width: 8),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(8)),
                    child: Text(status.label,
                        style: TextStyle(
                            fontSize: 10,
                            color: color,
                            fontWeight: FontWeight.w600)),
                  ),
                ]),
              );
            }),
            if (items.length > 3) ...[
              const SizedBox(height: 6),
              Text('+${items.length - 3} more courses',
                  style:
                      const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ],
        ),
      ),
    );
  }
}
