// lib/presentation/hr/analytics/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/usecases/get_org_skill_gaps_use_case.dart';
import '../../employee/dashboard/provider.dart';

final _skillGapsUc = const GetOrgSkillGapsUseCase();

class HrAnalyticsScreen extends ConsumerWidget {
  const HrAnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) => skillsAsync.when(
          loading: () => const LoadingView(),
          error: (e, _) => Center(child: Text('$e')),
          data: (skills) {
            final employees = allEmps;
            final roleList = roles;
            final gaps = _skillGapsUc.call(employees: employees, roles: roleList, skills: skills);

            // Dept distribution
            final deptCount = <String, int>{};
            for (final emp in employees) {
              deptCount[emp.department] = (deptCount[emp.department] ?? 0) + 1;
            }

            // Level distribution
            final levelCount = <RoleLevel, int>{};
            for (final role in roleList) {
              levelCount[role.level] = (levelCount[role.level] ?? 0) + 1;
            }

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _SectionTitle('Employees by Department'),
                SizedBox(height: 220, child: _DeptBarChart(deptCount: deptCount)),
                const SizedBox(height: 24),
                _SectionTitle('Role Level Distribution'),
                SizedBox(height: 200, child: _LevelPieChart(levelCount: levelCount)),
                const SizedBox(height: 24),
                _SectionTitle('Top Skill Gaps (Demand vs Supply)'),
                SizedBox(height: 220, child: _SkillGapChart(gaps: gaps)),
                const SizedBox(height: 24),
                _SectionTitle('Monthly Headcount Trend'),
                SizedBox(height: 200, child: _HeadcountChart()),
              ]),
            );
          },
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
  );
}

class _DeptBarChart extends StatelessWidget {
  final Map<String, int> deptCount;
  const _DeptBarChart({required this.deptCount});

  @override
  Widget build(BuildContext context) {
    final entries = deptCount.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    final top = entries.take(6).toList();
    return BarChart(BarChartData(
      gridData: const FlGridData(show: true),
      titlesData: FlTitlesData(
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) {
          if (v.toInt() >= top.length) return const Text('');
          final label = top[v.toInt()].key;
          return Padding(padding: const EdgeInsets.only(top: 4), child: Text(label.substring(0, label.length > 6 ? 6 : label.length), style: const TextStyle(fontSize: 9)));
        }, reservedSize: 28)),
        leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 24)),
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      ),
      barGroups: List.generate(top.length, (i) => BarChartGroupData(x: i, barRods: [BarChartRodData(toY: top[i].value.toDouble(), color: AppColors.primary, width: 20, borderRadius: BorderRadius.circular(4))])),
    ));
  }
}

class _LevelPieChart extends StatelessWidget {
  final Map<RoleLevel, int> levelCount;
  const _LevelPieChart({required this.levelCount});

  @override
  Widget build(BuildContext context) {
    final colors = [AppColors.success, AppColors.primary, AppColors.warning, AppColors.riskHigh, AppColors.riskCritical];
    final entries = levelCount.entries.toList();
    return PieChart(PieChartData(
      sections: List.generate(entries.length, (i) => PieChartSectionData(
        value: entries[i].value.toDouble(),
        color: colors[i % colors.length],
        title: '${entries[i].key.name}\n${entries[i].value}',
        titleStyle: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold),
        radius: 60,
      )),
      centerSpaceRadius: 40,
    ));
  }
}

class _SkillGapChart extends StatelessWidget {
  final List gaps;
  const _SkillGapChart({required this.gaps});

  @override
  Widget build(BuildContext context) {
    final top = gaps.take(6).toList();
    return BarChart(BarChartData(
      gridData: const FlGridData(show: true),
      titlesData: FlTitlesData(
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) {
          if (v.toInt() >= top.length) return const Text('');
          final name = top[v.toInt()].skill.name as String;
          return Padding(padding: const EdgeInsets.only(top: 4), child: Text(name.substring(0, name.length > 8 ? 8 : name.length), style: const TextStyle(fontSize: 9)));
        }, reservedSize: 28)),
        leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 24)),
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      ),
      barGroups: List.generate(top.length, (i) => BarChartGroupData(x: i, barRods: [
        BarChartRodData(toY: (top[i].demand as int).toDouble(), color: AppColors.riskHigh, width: 10, borderRadius: BorderRadius.circular(4)),
        BarChartRodData(toY: top[i].avgSupply as double, color: AppColors.success, width: 10, borderRadius: BorderRadius.circular(4)),
      ])),
    ));
  }
}

class _HeadcountChart extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final data = [42.0, 43.0, 45.0, 45.0, 47.0, 48.0, 49.0, 50.0, 50.0, 50.0, 50.0, 50.0];
    return LineChart(LineChartData(
      gridData: const FlGridData(show: true),
      titlesData: FlTitlesData(
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) {
          final months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
          final i = v.toInt();
          return i >= 0 && i < months.length ? Text(months[i], style: const TextStyle(fontSize: 10)) : const Text('');
        }, reservedSize: 20)),
        leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 28)),
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      ),
      lineBarsData: [LineChartBarData(
        spots: List.generate(data.length, (i) => FlSpot(i.toDouble(), data[i])),
        color: AppColors.primary, barWidth: 2, isCurved: true,
        belowBarData: BarAreaData(show: true, color: AppColors.primary.withOpacity(0.1)),
        dotData: const FlDotData(show: false),
      )],
    ));
  }
}
