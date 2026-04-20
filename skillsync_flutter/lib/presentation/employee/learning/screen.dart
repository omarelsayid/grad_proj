// lib/presentation/employee/learning/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/learning_item.dart';
import '../../../domain/entities/learning_progress.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/get_suggested_learning_use_case.dart';
import '../../../services/api_client.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';
import 'progress_provider.dart';

const _roleFitUc = CalculateRoleFitUseCase();
const _learningUc = GetSuggestedLearningUseCase(_roleFitUc);

/// Calls /ml/learning-path and returns itemId → priority (1=high,2=medium,3=low).
/// Returns null silently when ML service is unreachable.
final mlLearningRankingProvider = FutureProvider<Map<String, int>?>((ref) async {
  final employee = ref.watch(authProvider).currentUser;
  if (employee == null) return null;

  final roles          = await ref.watch(employeeRolesProvider.future);
  final items          = await ref.watch(learningItemsProvider.future);
  final selectedRoleId = ref.watch(selectedTargetRoleProvider);

  final roleMap   = {for (final r in roles) r.id: r};
  final targetRole = roleMap[selectedRoleId] ?? roleMap[employee.roleId];
  if (targetRole == null) return null;

  final fitResult = _roleFitUc.call(employee, targetRole);
  if (fitResult.missingSkillIds.isEmpty) return null;

  try {
    final data = await ApiClient.instance.getMlLearningPath({
      'employee_id':          employee.id,
      'job_role_id':          targetRole.id,
      'employee_avg_score':   employee.satisfactionScore.clamp(0, 100),
      'employee_courses_done': 0,
      'missing_skills': fitResult.missingSkillIds.map((sid) {
        final req = targetRole.requiredSkills.firstWhere(
          (r) => r.skillId == sid,
          orElse: () => RoleSkillRequirement(skillId: sid, minProficiency: 3),
        );
        return {
          'skill_id':          sid,
          'gap':               req.minProficiency.toDouble(),
          'importance_weight': 0.8,
          'complexity_level':  req.minProficiency >= 4 ? 3 : req.minProficiency >= 2 ? 2 : 1,
        };
      }).toList(),
      'available_resources': items.map((item) => {
        'resource_id':   item.id,
        'title':         item.title,
        'skill_id':      item.skillId,
        'skill_level':   item.priority == 1 ? 'Advanced' : item.priority == 2 ? 'Intermediate' : 'Beginner',
        'duration_hours': item.estimatedHours > 0 ? item.estimatedHours.toDouble() : 1.0,
      }).toList(),
    });

    final recs   = data['recommendations'] as List<dynamic>;
    final result = <String, int>{};
    for (final rec in recs) {
      final r = rec as Map<String, dynamic>;
      result[r['resource_id'] as String] = switch (r['priority'] as String? ?? 'low') {
        'high'   => 1,
        'medium' => 2,
        _        => 3,
      };
    }
    return result.isEmpty ? null : result;
  } catch (_) {
    return null;
  }
});

final learningItemsProvider = FutureProvider<List<LearningItem>>((ref) async {
  final repo = ref.read(skillRepositoryProvider);
  return repo.getAllLearningItems();
});

class EmployeeLearningScreen extends ConsumerStatefulWidget {
  const EmployeeLearningScreen({super.key});

  @override
  ConsumerState<EmployeeLearningScreen> createState() =>
      _EmployeeLearningScreenState();
}

class _EmployeeLearningScreenState
    extends ConsumerState<EmployeeLearningScreen> {
  LearningStatus? _filter;

  @override
  Widget build(BuildContext context) {
    final employee = ref.watch(authProvider).currentUser;
    if (employee == null) return const LoadingView();

    final learningAsync  = ref.watch(learningItemsProvider);
    final rolesAsync     = ref.watch(employeeRolesProvider);
    final selectedRoleId = ref.watch(selectedTargetRoleProvider);
    final progressMap    = ref.watch(learningProgressProvider);
    final mlPriorities   = ref.watch(mlLearningRankingProvider).valueOrNull;

    return learningAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allItems) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) {
          final roleMap = {for (final r in roles) r.id: r};
          final targetRole =
              roleMap[selectedRoleId] ?? roleMap[employee.roleId];

          var items = targetRole != null
              ? _learningUc.call(
                  employee: employee,
                  targetRole: targetRole,
                  catalog: allItems,
                )
              : allItems;

          if (_filter != null) {
            items = items
                .where((item) =>
                    (progressMap[item.id] ?? LearningStatus.notStarted) ==
                    _filter)
                .toList();
          }

          final totalAll = allItems.length;
          final completed = progressMap.values
              .where((v) => v == LearningStatus.completed)
              .length;
          final inProgress = progressMap.values
              .where((v) => v == LearningStatus.inProgress)
              .length;

          return Column(
            children: [
              _ProgressHeader(
                  total: totalAll,
                  completed: completed,
                  inProgress: inProgress,
                  mlActive: mlPriorities != null),
              _FilterRow(
                  current: _filter,
                  onChanged: (f) => setState(() => _filter = f)),
              Expanded(
                child: items.isEmpty
                    ? const EmptyState(
                        icon: Icons.school_outlined,
                        title: 'No courses match this filter',
                        subtitle: 'Try a different filter or select another target role.')
                    : _buildGroupedList(items, progressMap, mlPriorities: mlPriorities),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildGroupedList(
      List<LearningItem> items, Map<String, LearningStatus> progressMap,
      {Map<String, int>? mlPriorities}) {
    final grouped = <int, List<LearningItem>>{};
    for (final item in items) {
      final p = mlPriorities?[item.id] ?? item.priority;
      grouped[p] ??= [];
      grouped[p]!.add(item);
    }
    final priorities = grouped.keys.toList()..sort();

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: priorities.length,
      itemBuilder: (ctx, i) {
        final p = priorities[i];
        final group = grouped[p]!;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: EdgeInsets.only(bottom: 12, top: i > 0 ? 16 : 0),
              child: Row(children: [
                Container(
                  width: 28,
                  height: 28,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: _priorityColor(p).withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Text('P$p',
                      style: TextStyle(
                          color: _priorityColor(p),
                          fontWeight: FontWeight.bold,
                          fontSize: 11)),
                ),
                const SizedBox(width: 8),
                Text(_priorityLabel(p),
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 15)),
              ]),
            ),
            ...group.map((item) => _LearningCard(
                  item: item,
                  status:
                      progressMap[item.id] ?? LearningStatus.notStarted,
                  onStatusChanged: (s) => ref
                      .read(learningProgressProvider.notifier)
                      .setStatus(item.id, s),
                )),
          ],
        );
      },
    );
  }

  Color _priorityColor(int p) {
    switch (p) {
      case 1:
        return AppColors.riskHigh;
      case 2:
        return AppColors.warning;
      default:
        return AppColors.success;
    }
  }

  String _priorityLabel(int p) {
    switch (p) {
      case 1:
        return 'High Priority';
      case 2:
        return 'Medium Priority';
      default:
        return 'Low Priority';
    }
  }
}

// ── Progress header ────────────────────────────────────────────────────────────
class _ProgressHeader extends StatelessWidget {
  final int total;
  final int completed;
  final int inProgress;
  final bool mlActive;

  const _ProgressHeader(
      {required this.total,
      required this.completed,
      required this.inProgress,
      this.mlActive = false});

  @override
  Widget build(BuildContext context) {
    final pct = total > 0 ? completed / total : 0.0;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.04),
        border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text('$completed / $total completed',
              style:
                  const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          const Spacer(),
          if (mlActive)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.psychology_outlined, size: 11, color: AppColors.accent),
                SizedBox(width: 3),
                Text('AI-Ranked', style: TextStyle(fontSize: 10, color: AppColors.accent, fontWeight: FontWeight.bold)),
              ]),
            ),
          if (inProgress > 0)
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.warning.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text('$inProgress in progress',
                  style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.warning,
                      fontWeight: FontWeight.w600)),
            ),
        ]),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: pct,
            backgroundColor: Colors.grey.shade200,
            color: AppColors.success,
            minHeight: 6,
          ),
        ),
      ]),
    );
  }
}

// ── Filter row ─────────────────────────────────────────────────────────────────
class _FilterRow extends StatelessWidget {
  final LearningStatus? current;
  final ValueChanged<LearningStatus?> onChanged;

  const _FilterRow({required this.current, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(children: [
        _chip(null, 'All'),
        _chip(LearningStatus.notStarted, 'Not Started'),
        _chip(LearningStatus.inProgress, 'In Progress'),
        _chip(LearningStatus.completed, 'Completed'),
      ]),
    );
  }

  Widget _chip(LearningStatus? value, String label) {
    final selected = current == value;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(label,
            style: TextStyle(
                fontSize: 12,
                fontWeight:
                    selected ? FontWeight.bold : FontWeight.normal)),
        selected: selected,
        onSelected: (_) => onChanged(value),
        showCheckmark: false,
      ),
    );
  }
}

// ── Learning card ──────────────────────────────────────────────────────────────
class _LearningCard extends StatelessWidget {
  final LearningItem item;
  final LearningStatus status;
  final ValueChanged<LearningStatus> onStatusChanged;

  const _LearningCard({
    required this.item,
    required this.status,
    required this.onStatusChanged,
  });

  Future<void> _openUrl() async {
    final uri = Uri.parse(item.url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Color get _typeColor {
    switch (item.type) {
      case LearningType.course:        return AppColors.primary;
      case LearningType.article:       return AppColors.secondary;
      case LearningType.certification: return AppColors.accent;
      case LearningType.project:       return AppColors.warning;
      case LearningType.mentorship:    return AppColors.success;
    }
  }

  String _targetDate(int hours) {
    final days = (hours / 2).ceil();
    final target = DateTime.now().add(Duration(days: days));
    return '${target.day}/${target.month}/${target.year}';
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: _openUrl,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title row
              Row(children: [
                Expanded(
                    child: Text(item.title,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600, fontSize: 14))),
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                      color: _typeColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12)),
                  child: Text(item.typeLabel,
                      style: TextStyle(
                          color: _typeColor,
                          fontSize: 11,
                          fontWeight: FontWeight.w600)),
                ),
              ]),
              const SizedBox(height: 3),
              // Platform
              Text(item.platform,
                  style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.primary,
                      fontWeight: FontWeight.w500)),
              const SizedBox(height: 6),
              // Description
              Text(item.description,
                  style:
                      const TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 10),
              // Meta row: duration + target date + status chip
              Row(children: [
                const Icon(Icons.access_time, size: 13, color: Colors.grey),
                const SizedBox(width: 4),
                Text(item.duration,
                    style: const TextStyle(fontSize: 12, color: Colors.grey)),
                if (item.estimatedHours > 0) ...[
                  const SizedBox(width: 10),
                  const Icon(Icons.flag_outlined, size: 13, color: Colors.grey),
                  const SizedBox(width: 4),
                  Text('Target: ${_targetDate(item.estimatedHours)}',
                      style:
                          const TextStyle(fontSize: 11, color: Colors.grey)),
                ],
                const Spacer(),
                _StatusChip(
                    status: status,
                    onTap: () => onStatusChanged(status.next)),
              ]),
              const SizedBox(height: 10),
              // Open button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _openUrl,
                  icon: const Icon(Icons.open_in_new, size: 14),
                  label: Text('Open on ${item.platform}',
                      style: const TextStyle(fontSize: 12)),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    side: BorderSide(
                        color: AppColors.primary.withValues(alpha: 0.4)),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Status chip (tappable to cycle status) ─────────────────────────────────────
class _StatusChip extends StatelessWidget {
  final LearningStatus status;
  final VoidCallback onTap;

  const _StatusChip({required this.status, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final (color, icon) = switch (status) {
      LearningStatus.notStarted => (Colors.grey, Icons.radio_button_unchecked),
      LearningStatus.inProgress => (AppColors.warning, Icons.pending_outlined),
      LearningStatus.completed  => (AppColors.success, Icons.check_circle_outline),
    };
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.35)),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(status.label,
              style: TextStyle(
                  fontSize: 11,
                  color: color,
                  fontWeight: FontWeight.w600)),
        ]),
      ),
    );
  }
}
