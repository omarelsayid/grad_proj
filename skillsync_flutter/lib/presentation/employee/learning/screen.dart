// lib/presentation/employee/learning/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/learning_item.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/get_suggested_learning_use_case.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

final _roleFitUc = const CalculateRoleFitUseCase();
final _learningUc = GetSuggestedLearningUseCase(_roleFitUc);

final learningItemsProvider = FutureProvider<List<LearningItem>>((ref) async {
  final repo = ref.read(skillRepositoryProvider);
  return repo.getAllLearningItems();
});

class EmployeeLearningScreen extends ConsumerWidget {
  const EmployeeLearningScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final employee = ref.watch(authProvider).currentUser;
    if (employee == null) return const LoadingView();

    final learningAsync = ref.watch(learningItemsProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);

    return learningAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allItems) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) {
          final roleMap = {for (final r in roles as List<Role>) r.id: r};
          final currentRole = roleMap[employee.roleId];

          final items = currentRole != null
              ? _learningUc.call(
                  employee: employee,
                  targetRole: currentRole,
                  catalog: allItems,
                )
              : allItems;

          if (items.isEmpty) {
            return const EmptyState(
              icon: Icons.school_outlined,
              title: 'No learning items match your gaps',
              subtitle: 'You meet all skill requirements for your current role!',
            );
          }

          final grouped = <int, List<LearningItem>>{};
          for (final item in items) {
            grouped[item.priority] ??= [];
            grouped[item.priority]!.add(item);
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: grouped.keys.length,
            itemBuilder: (ctx, i) {
              final priority = grouped.keys.toList()..sort();
              final p = priority[i];
              final group = grouped[p]!;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: EdgeInsets.only(bottom: 12, top: i > 0 ? 16 : 0),
                    child: Row(children: [
                      Container(
                        width: 28, height: 28,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: _priorityColor(p).withOpacity(0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Text('P$p', style: TextStyle(color: _priorityColor(p), fontWeight: FontWeight.bold, fontSize: 11)),
                      ),
                      const SizedBox(width: 8),
                      Text(_priorityLabel(p), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    ]),
                  ),
                  ...group.map((item) => _LearningCard(item: item)),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Color _priorityColor(int p) {
    switch (p) {
      case 1: return AppColors.riskHigh;
      case 2: return AppColors.warning;
      default: return AppColors.success;
    }
  }

  String _priorityLabel(int p) {
    switch (p) {
      case 1: return 'High Priority';
      case 2: return 'Medium Priority';
      default: return 'Low Priority';
    }
  }
}

class _LearningCard extends StatelessWidget {
  final LearningItem item;
  const _LearningCard({required this.item});

  Color get _typeColor {
    switch (item.type) {
      case LearningType.course: return AppColors.primary;
      case LearningType.certification: return AppColors.accent;
      case LearningType.project: return AppColors.warning;
      case LearningType.mentorship: return AppColors.secondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Expanded(child: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14))),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: _typeColor.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                child: Text(item.typeLabel, style: TextStyle(color: _typeColor, fontSize: 11, fontWeight: FontWeight.w600)),
              ),
            ]),
            const SizedBox(height: 6),
            Text(item.description, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 8),
            Row(children: [
              const Icon(Icons.access_time, size: 14, color: Colors.grey),
              const SizedBox(width: 4),
              Text(item.duration, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ]),
          ],
        ),
      ),
    );
  }
}
