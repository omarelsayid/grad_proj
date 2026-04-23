// lib/presentation/hr/audit/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/audit_log.dart';
import '../../auth/auth_provider.dart';

final _auditProvider = FutureProvider<List<AuditLog>>((ref) async {
  return ref.read(skillRepositoryProvider).getAuditLogs();
});

class HrAuditScreen extends ConsumerWidget {
  const HrAuditScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auditAsync = ref.watch(_auditProvider);

    return auditAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (logs) {
        if (logs.isEmpty) return const Center(child: Text('No audit logs found.'));

        return Column(children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: Theme.of(context).colorScheme.surfaceVariant.withValues(alpha:0.4),
            child: const Row(children: [
              Expanded(flex: 2, child: Text('Action', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
              Expanded(flex: 2, child: Text('Entity', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
              Expanded(flex: 2, child: Text('Performed By', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
              Expanded(flex: 2, child: Text('Timestamp', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
            ]),
          ),
          Expanded(child: ListView.builder(
            itemCount: logs.length,
            itemBuilder: (ctx, i) {
              final log = logs[i];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.grey.withValues(alpha:0.1)))),
                child: Row(children: [
                  Expanded(flex: 2, child: _ActionBadge(action: log.action)),
                  Expanded(flex: 2, child: Text(log.entityType, style: const TextStyle(fontSize: 12))),
                  Expanded(flex: 2, child: Text(log.performedBy, style: const TextStyle(fontSize: 12))),
                  Expanded(flex: 2, child: Text(AppDateUtils.formatDate(log.timestamp), style: const TextStyle(fontSize: 11, color: Colors.grey))),
                ]),
              );
            },
          )),
        ]);
      },
    );
  }
}

class _ActionBadge extends StatelessWidget {
  final String action;
  const _ActionBadge({required this.action});

  Color get _color {
    if (action.contains('APPROVE') || action.contains('ADD')) return AppColors.success;
    if (action.contains('REJECT') || action.contains('DELETE')) return AppColors.riskHigh;
    if (action.contains('UPDATE') || action.contains('PROCESS')) return AppColors.warning;
    return AppColors.info;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(color: _color.withValues(alpha:0.12), borderRadius: BorderRadius.circular(8)),
      child: Text(action, style: TextStyle(color: _color, fontSize: 10, fontWeight: FontWeight.w600)),
    );
  }
}
