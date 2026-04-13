// lib/presentation/employee/dashboard/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../auth/auth_provider.dart';
import 'provider.dart';
import 'widgets/welcome_banner.dart';

const _roleFitUc = CalculateRoleFitUseCase();

class EmployeeDashboardScreen extends ConsumerStatefulWidget {
  const EmployeeDashboardScreen({super.key});

  @override
  ConsumerState<EmployeeDashboardScreen> createState() => _EmployeeDashboardScreenState();
}

class _EmployeeDashboardScreenState extends ConsumerState<EmployeeDashboardScreen> {
  String? _selectedRoleId;

  @override
  Widget build(BuildContext context) {
    final employee = ref.watch(authProvider).currentUser;
    if (employee == null) return const LoadingView();

    final skillsAsync = ref.watch(employeeSkillsProvider);
    final rolesAsync = ref.watch(employeeRolesProvider);

    return skillsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (allSkills) => rolesAsync.when(
        loading: () => const LoadingView(),
        error: (e, _) => Center(child: Text('$e')),
        data: (roles) {
          final skillMap = {for (final s in allSkills) s.id: s};
          final roleMap = {for (final r in roles) r.id: r};
          final currentRole = roleMap[employee.roleId];
          final fitScore = currentRole != null
              ? _roleFitUc.call(employee, currentRole).fitScore
              : 0;

          final masteredCount = employee.skills.where((s) => s.proficiency >= 4).length;
          final totalSkills = employee.skills.length;
          final masteryRatio = totalSkills > 0 ? masteredCount / totalSkills : 0.0;
          final growthPotential = masteryRatio < 0.3
              ? 'High'
              : masteryRatio < 0.65
                  ? 'Medium'
                  : 'Low';

          final targetRole = _selectedRoleId != null ? roleMap[_selectedRoleId] : null;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              WelcomeBanner(employee: employee),
              const SizedBox(height: 16),

              // ── 4 stat cards in 2×2 compact grid ──────────────────────
              GridView.count(
                crossAxisCount: 2, shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 8, crossAxisSpacing: 8,
                childAspectRatio: 2.3,
                children: [
                  _MiniStat(
                    icon: Icons.track_changes,
                    label: 'Role-Fit Score',
                    value: fitScore > 0 ? '$fitScore%' : 'Select role',
                    sub: fitScore > 0 ? 'Match score' : 'Choose a target role',
                    color: AppColors.primary,
                  ),
                  _MiniStat(
                    icon: Icons.military_tech_outlined,
                    label: 'Skills Mastered',
                    value: '$masteredCount/$totalSkills',
                    sub: 'Proficiency 4+',
                    color: AppColors.success,
                  ),
                  _MiniStat(
                    icon: Icons.trending_up,
                    label: 'Growth Potential',
                    value: growthPotential,
                    sub: 'Based on skill trajectory',
                    color: AppColors.secondary,
                  ),
                  _MiniStat(
                    icon: Icons.menu_book_outlined,
                    label: 'Learning Hours',
                    value: '24',
                    sub: 'This quarter',
                    color: AppColors.warning,
                    onTap: () => context.go('/employee/learning'),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // ── Skill Profile ──────────────────────────────────────────
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text('Your Skill Profile', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                TextButton(onPressed: () => context.go('/employee/skills'), child: const Text('See all')),
              ]),
              const SizedBox(height: 8),
              GridView.count(
                crossAxisCount: 2, shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 8, crossAxisSpacing: 8,
                childAspectRatio: 1.9,
                children: employee.skills.take(4).map((es) {
                  final skill = skillMap[es.skillId];
                  if (skill == null) return const SizedBox.shrink();
                  return _SkillProfileCard(empSkillProficiency: es.proficiency, skill: skill);
                }).toList(),
              ),

              const SizedBox(height: 24),

              // ── Skill Gap Analysis ────────────────────────────────────
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text('Skill Gap Analysis', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                DropdownButton<String>(
                  hint: const Text('Select target role', style: TextStyle(fontSize: 12)),
                  value: _selectedRoleId,
                  isDense: true,
                  items: roles.map((r) => DropdownMenuItem(
                    value: r.id,
                    child: Text(r.title, style: const TextStyle(fontSize: 12)),
                  )).toList(),
                  onChanged: (v) => setState(() => _selectedRoleId = v),
                ),
              ]),
              const SizedBox(height: 12),
              if (targetRole != null)
                _SkillGapPanel(employee: employee, role: targetRole, skillMap: skillMap)
              else
                _NoRoleSelected(),

              const SizedBox(height: 16),
            ]),
          );
        },
      ),
    );
  }
}

// ── Mini stat card ─────────────────────────────────────────────────────────────
class _MiniStat extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String sub;
  final Color color;
  final VoidCallback? onTap;

  const _MiniStat({
    required this.icon,
    required this.label,
    required this.value,
    required this.sub,
    required this.color,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          child: Row(children: [
            Container(
              width: 34, height: 34,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.12), shape: BoxShape.circle),
              child: Icon(icon, color: color, size: 17),
            ),
            const SizedBox(width: 8),
            Expanded(child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(value, style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: color)),
                Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey), overflow: TextOverflow.ellipsis),
              ],
            )),
          ]),
        ),
      ),
    );
  }
}

// ── Skill profile card ─────────────────────────────────────────────────────────
class _SkillProfileCard extends StatelessWidget {
  final int empSkillProficiency;
  final Skill skill;

  const _SkillProfileCard({required this.empSkillProficiency, required this.skill});

  Color get _categoryColor {
    switch (skill.category) {
      case SkillCategory.technical:   return AppColors.primary;
      case SkillCategory.soft:        return AppColors.success;
      case SkillCategory.management:  return AppColors.secondary;
      case SkillCategory.domain:      return AppColors.warning;
    }
  }

  Color get _barColor {
    if (empSkillProficiency >= 4) return AppColors.success;
    if (empSkillProficiency >= 3) return AppColors.warning;
    return AppColors.riskHigh;
  }

  String get _categoryLabel {
    switch (skill.category) {
      case SkillCategory.technical:   return 'technical';
      case SkillCategory.soft:        return 'soft';
      case SkillCategory.management:  return 'management';
      case SkillCategory.domain:      return 'domain';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Expanded(
              child: Text(skill.name,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Text('$empSkillProficiency/5',
              style: TextStyle(fontWeight: FontWeight.bold, color: _barColor, fontSize: 13),
            ),
          ]),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _categoryColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(_categoryLabel, style: TextStyle(fontSize: 10, color: _categoryColor, fontWeight: FontWeight.w600)),
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: empSkillProficiency / 5,
              backgroundColor: Colors.grey.shade200,
              color: _barColor,
              minHeight: 6,
            ),
          ),
        ]),
      ),
    );
  }
}

// ── Skill gap panel ────────────────────────────────────────────────────────────
class _SkillGapPanel extends StatelessWidget {
  final Employee employee;
  final Role role;
  final Map<String, Skill> skillMap;

  const _SkillGapPanel({required this.employee, required this.role, required this.skillMap});

  @override
  Widget build(BuildContext context) {
    final empSkillMap = {for (final s in employee.skills) s.skillId: s.proficiency};

    return Column(
      children: role.requiredSkills.take(6).map((req) {
        final skill = skillMap[req.skillId];
        if (skill == null) return const SizedBox.shrink();
        final current = empSkillMap[req.skillId] ?? 0;
        final gap = req.minProficiency - current;
        final barColor = gap <= 0 ? AppColors.success : gap == 1 ? AppColors.warning : AppColors.riskHigh;

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Expanded(child: Text(skill.name, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13))),
                Text(
                  gap <= 0 ? '✓ Met' : 'Gap: $gap',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: barColor),
                ),
              ]),
              const SizedBox(height: 6),
              Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('You: $current/5', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                    const SizedBox(height: 2),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: current / 5,
                        backgroundColor: Colors.grey.shade200,
                        color: barColor,
                        minHeight: 5,
                      ),
                    ),
                  ]),
                ),
                const SizedBox(width: 12),
                Text('Req: ${req.minProficiency}/5', style: const TextStyle(fontSize: 10, color: Colors.grey)),
              ]),
            ]),
          ),
        );
      }).toList(),
    );
  }
}

// ── No role selected placeholder ───────────────────────────────────────────────
class _NoRoleSelected extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 140,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(Icons.track_changes, size: 36, color: Colors.grey.shade400),
        const SizedBox(height: 8),
        Text('Choose Your Target Role', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.grey.shade600)),
        const SizedBox(height: 4),
        Text('Select a role above to see your skill gap analysis', style: TextStyle(fontSize: 12, color: Colors.grey.shade400), textAlign: TextAlign.center),
      ]),
    );
  }
}
