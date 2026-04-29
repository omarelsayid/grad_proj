// lib/presentation/hr/replacements/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/employee.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../../domain/usecases/find_replacement_candidates_use_case.dart';
import '../../employee/dashboard/provider.dart';

const _roleFitUc = CalculateRoleFitUseCase();
const _replacementUc = FindReplacementCandidatesUseCase(_roleFitUc);

class HrReplacementsScreen extends ConsumerStatefulWidget {
  const HrReplacementsScreen({super.key});
  @override
  ConsumerState<HrReplacementsScreen> createState() => _State();
}

class _State extends ConsumerState<HrReplacementsScreen> {
  String? _selectedDepartingId;
  bool _sameDeptOnly = false;

  @override
  Widget build(BuildContext context) {
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
            final empList = (allEmps as List).cast<Employee>();
            final roleMap = {for (final r in (roles as List).cast<Role>()) r.id: r};
            _selectedDepartingId ??= empList.first.id;

            final departing = empList.firstWhere(
              (e) => e.id == _selectedDepartingId,
              orElse: () => empList.first,
            );
            final role = roleMap[departing.roleId];

            final pool = _sameDeptOnly
                ? empList.where((e) => e.department == departing.department).toList()
                : empList;

            final candidates = role != null
                ? _replacementUc.call(
                    departing: departing,
                    allEmployees: pool,
                    role: role,
                    allSkills: (skills as List).cast<Skill>(),
                    limit: 10,
                  )
                : <ReplacementCandidate>[];

            final deptCount = empList.map((e) => e.department).toSet().length;

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _StatsBanner(
                  totalSearched: pool.length - 1,
                  deptCount: _sameDeptOnly ? 1 : deptCount,
                  roleName: role?.title ?? '—',
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _selectedDepartingId,
                  decoration: const InputDecoration(
                    labelText: 'Departing Employee',
                    prefixIcon: Icon(Icons.person_remove_outlined),
                  ),
                  items: empList
                      .map((e) => DropdownMenuItem(
                            value: e.id,
                            child: Text('${e.name} (${e.currentRole})'),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _selectedDepartingId = v),
                ),
                const SizedBox(height: 12),
                Row(children: [
                  Switch(
                    value: _sameDeptOnly,
                    onChanged: (v) => setState(() => _sameDeptOnly = v),
                    activeThumbColor: AppColors.primary,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _sameDeptOnly
                          ? 'Same department only (${departing.department})'
                          : 'Company-wide search — all ${empList.length} employees',
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ]),
                const SizedBox(height: 16),
                if (role != null) ...[
                  Text(
                    'Replacement Candidates for "${role.title}"',
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Ranked by skill-fit score across ${pool.length - 1} candidates',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  const SizedBox(height: 12),
                ],
                if (candidates.isEmpty)
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('No candidates found.'),
                    ),
                  )
                else
                  ...candidates.map((c) => _CandidateCard(
                        candidate: c,
                        rank: candidates.indexOf(c) + 1,
                      )),
              ]),
            );
          },
        ),
      ),
    );
  }
}

class _StatsBanner extends StatelessWidget {
  final int totalSearched;
  final int deptCount;
  final String roleName;

  const _StatsBanner({
    required this.totalSearched,
    required this.deptCount,
    required this.roleName,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
      ),
      child: Row(children: [
        _Stat(label: 'Candidates Searched', value: '$totalSearched'),
        _divider(),
        _Stat(label: 'Departments', value: '$deptCount'),
        _divider(),
        _Stat(label: 'Open Role', value: roleName, flex: 2),
      ]),
    );
  }

  Widget _divider() => Container(
        width: 1,
        height: 36,
        color: AppColors.primary.withValues(alpha: 0.15),
        margin: const EdgeInsets.symmetric(horizontal: 12),
      );
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;
  final int flex;

  const _Stat({required this.label, required this.value, this.flex = 1});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      flex: flex,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value,
            style: const TextStyle(
                fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.primary)),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ]),
    );
  }
}

class _CandidateCard extends StatelessWidget {
  final ReplacementCandidate candidate;
  final int rank;

  const _CandidateCard({required this.candidate, required this.rank});

  String _readiness(int score) {
    if (score >= 75) return 'Ready';
    if (score >= 50) return 'Near Ready';
    if (score >= 25) return 'Needs Development';
    return 'Not Suitable';
  }

  Color _color(int score) {
    if (score >= 75) return AppColors.success;
    if (score >= 50) return AppColors.warning;
    if (score >= 25) return AppColors.riskHigh;
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(candidate.fitScore);
    final readiness = _readiness(candidate.fitScore);

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              width: 32,
              height: 32,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text('#$rank',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, color: AppColors.primary)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(candidate.employee.name,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                Row(children: [
                  Text(candidate.employee.currentRole,
                      style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(width: 6),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                    decoration: BoxDecoration(
                      color: Colors.blueGrey.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(candidate.employee.department,
                        style: const TextStyle(
                            fontSize: 10, color: Colors.blueGrey)),
                  ),
                ]),
              ]),
            ),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text('${candidate.fitScore}%',
                  style: TextStyle(
                      fontSize: 22, fontWeight: FontWeight.bold, color: color)),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(readiness,
                    style: TextStyle(
                        fontSize: 10,
                        color: color,
                        fontWeight: FontWeight.w600)),
              ),
            ]),
          ]),
          const SizedBox(height: 10),
          LinearProgressIndicator(
            value: candidate.fitScore / 100,
            backgroundColor: color.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
          const SizedBox(height: 10),
          Wrap(spacing: 6, runSpacing: 4, children: [
            ...candidate.matchingSkills
                .take(3)
                .map((s) => _Tag(label: s.name, color: AppColors.success)),
            ...candidate.missingSkills
                .take(2)
                .map((s) =>
                    _Tag(label: s.name, color: AppColors.riskHigh, dash: true)),
          ]),
        ]),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final Color color;
  final bool dash;

  const _Tag({required this.label, required this.color, this.dash = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: dash ? Border.all(color: color.withValues(alpha: 0.4)) : null,
      ),
      child: Text('${dash ? '- ' : '+ '}$label',
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
