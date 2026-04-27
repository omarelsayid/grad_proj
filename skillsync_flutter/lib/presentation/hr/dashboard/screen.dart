// lib/presentation/hr/dashboard/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/widgets/stat_card.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/turnover_risk_data.dart';
import '../../../domain/usecases/calculate_turnover_risk_use_case.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/get_org_skill_gaps_use_case.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../data/mock/mock_attendance.dart';
import '../../../data/mock/mock_static_data.dart';
import '../../employee/dashboard/provider.dart';

const _roleFitUc = CalculateRoleFitUseCase();
const _turnoverUc = CalculateTurnoverRiskUseCase(_roleFitUc);
const _skillGapsUc = GetOrgSkillGapsUseCase();

class HrDashboardScreen extends ConsumerWidget {
  const HrDashboardScreen({super.key});

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
            final roleMap = {for (final r in roleList) r.id: r};
            final gaps = _skillGapsUc.call(employees: employees, roles: roleList, skills: skills);
            final depts = employees.map((e) => e.department).toSet();

            // Compute top 4 turnover risks
            final List<TurnoverRiskData> riskData = employees.map((emp) {
              final role = roleMap[emp.roleId];
              final attendance = generateAttendance(emp.id);
              final leaves = mockLeaveRequests.where((l) => l.employeeId == emp.id).toList();
              return _turnoverUc.call(emp, role, attendance, leaves);
            }).toList()..sort((a, b) => b.riskScore.compareTo(a.riskScore));

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const _AnalyticsBanner(url: 'http://localhost:8501', label: 'HR Admin Analytics Dashboard'),
                const SizedBox(height: 14),
                // Compact 2×2 stat cards
                GridView.count(
                  crossAxisCount: 2, shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 8, crossAxisSpacing: 8,
                  childAspectRatio: 2.4,
                  children: [
                    StatCard(label: 'Total Employees', value: '${employees.length}', icon: Icons.people, iconColor: AppColors.primary, onTap: () => context.go('/hr/employees')),
                    StatCard(label: 'Departments', value: '${depts.length}', icon: Icons.account_tree, iconColor: AppColors.secondary, onTap: () => context.go('/hr/departments')),
                    StatCard(label: 'Open Roles', value: '${roleList.length}', icon: Icons.badge_outlined, iconColor: AppColors.accent, onTap: () => context.go('/hr/roles')),
                    StatCard(label: 'Skill Gaps', value: '${gaps.length}', icon: Icons.warning_outlined, iconColor: AppColors.warning, onTap: () => context.go('/hr/analytics')),
                  ],
                ),
                const SizedBox(height: 20),
                _buildTopGaps(context, gaps),
                const SizedBox(height: 20),
                _buildTurnoverRisks(context, riskData),
              ]),
            );
          },
        ),
      ),
    );
  }

  Widget _buildTopGaps(BuildContext context, List gaps) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text('Top Skill Gaps', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        TextButton(onPressed: () {}, child: const Text('Full analytics')),
      ]),
      ...gaps.take(4).map((g) => Card(
        margin: const EdgeInsets.only(bottom: 6),
        child: ListTile(
          dense: true,
          leading: const Icon(Icons.psychology_outlined, color: AppColors.warning, size: 20),
          title: Text(g.skill.name, style: const TextStyle(fontSize: 13)),
          subtitle: Text('${g.demand} roles require this'),
          trailing: Text('Avg: ${g.avgSupply.toStringAsFixed(1)}/5', style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ),
      )),
    ]);
  }

  Widget _buildTurnoverRisks(BuildContext context, List<TurnoverRiskData> riskData) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text('Turnover Risk (Top 4)', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        TextButton(onPressed: () => context.go('/hr/turnover'), child: const Text('See all')),
      ]),
      ...riskData.take(4).map((r) {
        final color = switch (r.riskLevel) {
          RiskLevel.critical => AppColors.riskCritical,
          RiskLevel.high     => AppColors.riskHigh,
          RiskLevel.medium   => AppColors.riskMedium,
          RiskLevel.low      => AppColors.riskLow,
        };
        return Card(
          margin: const EdgeInsets.only(bottom: 6),
          child: ListTile(
            dense: true,
            leading: CircleAvatar(radius: 16, child: Text(r.employee.name[0])),
            title: Text(r.employee.name, style: const TextStyle(fontSize: 13)),
            subtitle: Text(r.employee.currentRole, style: const TextStyle(fontSize: 11)),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(12)),
              child: Text(r.riskLevelLabel, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
            ),
          ),
        );
      }),
    ]);
  }
}

class _AnalyticsBanner extends StatelessWidget {
  final String url;
  final String label;
  const _AnalyticsBanner({required this.url, required this.label});

  Future<void> _launch() async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: _launch,
        borderRadius: BorderRadius.circular(12),
        child: Ink(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF1e3a5f), Color(0xFF1e40af)],
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(children: [
            const Icon(Icons.bar_chart_rounded, color: Colors.white, size: 26),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                const Text('Live data · ML insights · Streamlit', style: TextStyle(color: Colors.white70, fontSize: 11)),
              ]),
            ),
            const Icon(Icons.open_in_new, color: Colors.white70, size: 18),
          ]),
        ),
      ),
    );
  }
}
