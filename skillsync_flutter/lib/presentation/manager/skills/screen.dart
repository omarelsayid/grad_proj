// lib/presentation/manager/skills/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/skill.dart';
import '../../employee/dashboard/provider.dart';

class ManagerSkillsScreen extends ConsumerWidget {
  const ManagerSkillsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final empsAsync = ref.watch(allEmployeesProvider);
    final skillsAsync = ref.watch(employeeSkillsProvider);

    return empsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allEmps) => skillsAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (allSkills) {
          final teamEmps = (allEmps as List<Employee>).take(10).toList();
          final skillMap = {for (final s in allSkills as List<Skill>) s.id: s};

          // Compute avg proficiency per category
          final catSum = <SkillCategory, double>{};
          final catCount = <SkillCategory, int>{};
          for (final emp in teamEmps) {
            for (final es in emp.skills) {
              final skill = skillMap[es.skillId];
              if (skill == null) continue;
              catSum[skill.category] = (catSum[skill.category] ?? 0) + es.proficiency;
              catCount[skill.category] = (catCount[skill.category] ?? 0) + 1;
            }
          }

          final catData = SkillCategory.values.map((c) {
            final avg = catCount[c] != null ? (catSum[c] ?? 0) / catCount[c]! : 0.0;
            return (category: c, avg: avg);
          }).toList();

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Team Skill Distribution', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              SizedBox(height: 200, child: BarChart(_buildChart(catData))),
              const SizedBox(height: 24),
              ...catData.map((d) => _CategoryCard(category: d.category, avg: d.avg)),
            ]),
          );
        },
      ),
    );
  }

  BarChartData _buildChart(List catData) {
    final colors = [AppColors.skillTechnical, AppColors.skillSoft, AppColors.skillManagement, AppColors.skillDomain];
    return BarChartData(
      gridData: const FlGridData(show: true),
      titlesData: FlTitlesData(
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) {
          final labels = ['Tech', 'Soft', 'Mgmt', 'Domain'];
          return Text(labels[v.toInt() % labels.length], style: const TextStyle(fontSize: 10));
        })),
        leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 28)),
        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
      ),
      barGroups: List.generate(catData.length, (i) => BarChartGroupData(
        x: i,
        barRods: [BarChartRodData(toY: (catData[i] as dynamic).avg, color: colors[i % colors.length], width: 28, borderRadius: BorderRadius.circular(4))],
      )),
      maxY: 5,
    );
  }
}

class _CategoryCard extends StatelessWidget {
  final SkillCategory category;
  final double avg;
  const _CategoryCard({required this.category, required this.avg});

  Color get _color {
    switch (category) {
      case SkillCategory.technical: return AppColors.skillTechnical;
      case SkillCategory.soft: return AppColors.skillSoft;
      case SkillCategory.management: return AppColors.skillManagement;
      case SkillCategory.domain: return AppColors.skillDomain;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(category.name.toUpperCase(), style: TextStyle(fontWeight: FontWeight.bold, color: _color, fontSize: 12)),
            Text('${avg.toStringAsFixed(2)} / 5', style: TextStyle(fontWeight: FontWeight.bold, color: _color)),
          ]),
          const SizedBox(height: 6),
          LinearProgressIndicator(value: avg / 5, backgroundColor: _color.withOpacity(0.1), valueColor: AlwaysStoppedAnimation<Color>(_color), minHeight: 6),
        ]),
      ),
    );
  }
}
