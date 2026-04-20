// lib/presentation/hr/turnover/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/turnover_risk_data.dart';
import '../../../domain/usecases/calculate_turnover_risk_use_case.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../data/mock/mock_attendance.dart';
import '../../../data/mock/mock_static_data.dart';
import '../../employee/dashboard/provider.dart';
import '../ml_providers.dart';

final _roleFitUc = const CalculateRoleFitUseCase();
final _turnoverUc = CalculateTurnoverRiskUseCase(_roleFitUc);

class HrTurnoverScreen extends ConsumerStatefulWidget {
  const HrTurnoverScreen({super.key});
  @override ConsumerState<HrTurnoverScreen> createState() => _State();
}

class _State extends ConsumerState<HrTurnoverScreen> {
  String _deptFilter = 'All';
  String _riskFilter = 'All';

  @override
  Widget build(BuildContext context) {
    final empsAsync  = ref.watch(allEmployeesProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);
    final mlAsync    = ref.watch(mlTurnoverProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error:   (e, _) => Center(child: Text('$e')),
      data: (allEmps) => rolesAsync.when(
        loading: () => const LoadingView(),
        error:   (e, _) => Center(child: Text('$e')),
        data: (roles) {
          final mlMap   = mlAsync.valueOrNull ?? {};
          final roleMap = {for (final r in roles) r.id: r};

          final allRiskData = allEmps.map((emp) {
            final role       = roleMap[emp.roleId];
            final attendance = generateAttendance(emp.id);
            final leaves     = mockLeaveRequests.where((l) => l.employeeId == emp.id).toList();
            final local      = _turnoverUc.call(emp, role, attendance, leaves);
            final ml         = mlMap[emp.id];
            if (ml == null) return local;
            return TurnoverRiskData(
              employee:        local.employee,
              riskScore:       ml.riskScore,
              riskLevel:       ml.riskLevel,
              factorBreakdown: local.factorBreakdown,
            );
          }).toList()..sort((a, b) => b.riskScore.compareTo(a.riskScore));

          final depts      = ['All', ...{for (final e in allEmps) e.department}];
          final riskLevels = ['All', 'low', 'medium', 'high', 'critical'];

          final filtered = allRiskData.where((r) {
            final matchDept = _deptFilter == 'All' || r.employee.department == _deptFilter;
            final matchRisk = _riskFilter == 'All' || r.riskLevel.name == _riskFilter;
            return matchDept && matchRisk;
          }).toList();

          final levelDist = <RiskLevel, int>{};
          for (final r in allRiskData) {
            levelDist[r.riskLevel] = (levelDist[r.riskLevel] ?? 0) + 1;
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              // ML status banner
              if (mlMap.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.success.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
                  ),
                  child: Row(children: [
                    const Icon(Icons.psychology_outlined, size: 14, color: AppColors.success),
                    const SizedBox(width: 6),
                    Text(
                      'ML Model — ${mlMap.length}/${allEmps.length} employees scored by trained model',
                      style: const TextStyle(fontSize: 11, color: AppColors.success, fontWeight: FontWeight.w600),
                    ),
                  ]),
                ),
                const SizedBox(height: 16),
              ],
              _buildPieChart(context, levelDist),
              const SizedBox(height: 20),
              _buildFilters(depts, riskLevels),
              const SizedBox(height: 12),
              Text('${filtered.length} employees', style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 8),
              ...filtered.map((r) => _RiskCard(riskData: r, mlEntry: mlMap[r.employee.id])),
            ]),
          );
        },
      ),
    );
  }

  Widget _buildPieChart(BuildContext context, Map<RiskLevel, int> levelDist) {
    final colorMap = {
      RiskLevel.low:      AppColors.riskLow,
      RiskLevel.medium:   AppColors.riskMedium,
      RiskLevel.high:     AppColors.riskHigh,
      RiskLevel.critical: AppColors.riskCritical,
    };
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Risk Distribution', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      SizedBox(height: 180, child: Row(children: [
        Expanded(child: PieChart(PieChartData(
          sections: levelDist.entries.map((e) => PieChartSectionData(
            value: e.value.toDouble(),
            color: colorMap[e.key] ?? Colors.grey,
            title: '${e.key.name}\n${e.value}',
            titleStyle: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold),
            radius: 55,
          )).toList(),
          centerSpaceRadius: 30,
        ))),
        const SizedBox(width: 16),
        Column(mainAxisAlignment: MainAxisAlignment.center, children: levelDist.entries.map((e) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Container(width: 12, height: 12, decoration: BoxDecoration(color: colorMap[e.key] ?? Colors.grey, shape: BoxShape.circle)),
            const SizedBox(width: 6),
            Text('${e.key.name}: ${e.value}', style: const TextStyle(fontSize: 12)),
          ]),
        )).toList()),
      ])),
    ]);
  }

  Widget _buildFilters(List<String> depts, List<String> riskLevels) {
    return Row(children: [
      Expanded(child: DropdownButtonFormField<String>(
        initialValue: _deptFilter, isDense: true,
        decoration: const InputDecoration(labelText: 'Department'),
        items: depts.map((d) => DropdownMenuItem(value: d, child: Text(d, style: const TextStyle(fontSize: 12)))).toList(),
        onChanged: (v) => setState(() => _deptFilter = v!),
      )),
      const SizedBox(width: 8),
      Expanded(child: DropdownButtonFormField<String>(
        initialValue: _riskFilter, isDense: true,
        decoration: const InputDecoration(labelText: 'Risk Level'),
        items: riskLevels.map((r) => DropdownMenuItem(value: r, child: Text(r, style: const TextStyle(fontSize: 12)))).toList(),
        onChanged: (v) => setState(() => _riskFilter = v!),
      )),
    ]);
  }
}

class _RiskCard extends StatelessWidget {
  final TurnoverRiskData riskData;
  final MlTurnoverEntry? mlEntry;
  const _RiskCard({required this.riskData, this.mlEntry});

  Color get _color => switch (riskData.riskLevel) {
    RiskLevel.critical => AppColors.riskCritical,
    RiskLevel.high     => AppColors.riskHigh,
    RiskLevel.medium   => AppColors.riskMedium,
    RiskLevel.low      => AppColors.riskLow,
  };

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            CircleAvatar(radius: 18, child: Text(riskData.employee.name[0])),
            const SizedBox(width: 10),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(riskData.employee.name, style: const TextStyle(fontWeight: FontWeight.bold)),
              Text('${riskData.employee.currentRole} • ${riskData.employee.department}',
                  style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ])),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(riskData.riskLevelLabel,
                    style: TextStyle(color: _color, fontWeight: FontWeight.bold, fontSize: 12)),
              ),
              Text('${riskData.riskScore.toStringAsFixed(0)} pts',
                  style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ]),
          ]),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: (riskData.riskScore / 100).clamp(0.0, 1.0),
            backgroundColor: _color.withValues(alpha: 0.12),
            valueColor: AlwaysStoppedAnimation<Color>(_color),
            minHeight: 4,
          ),
          const SizedBox(height: 8),
          // ML top factors (when ML is active)
          if (mlEntry != null && mlEntry!.topFactors.isNotEmpty) ...[
            Wrap(spacing: 6, runSpacing: 4, children: mlEntry!.topFactors.map((f) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: _color.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(f, style: TextStyle(fontSize: 10, color: _color)),
            )).toList()),
          ] else ...[
            // Local heuristic factors
            Wrap(spacing: 6, runSpacing: 4, children: riskData.factorBreakdown
                .where((f) => f.triggered)
                .map((f) => Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _color.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(f.factor, style: TextStyle(fontSize: 10, color: _color)),
                )).toList()),
          ],
        ]),
      ),
    );
  }
}
