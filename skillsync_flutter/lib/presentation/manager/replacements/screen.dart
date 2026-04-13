// lib/presentation/manager/replacements/screen.dart
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

final _roleFitUc = const CalculateRoleFitUseCase();
final _replacementUc = FindReplacementCandidatesUseCase(_roleFitUc);

class ManagerReplacementsScreen extends ConsumerStatefulWidget {
  const ManagerReplacementsScreen({super.key});
  @override ConsumerState<ManagerReplacementsScreen> createState() => _State();
}

class _State extends ConsumerState<ManagerReplacementsScreen> {
  String? _selectedDepartingId;

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
            final teamEmps = (allEmps as List<Employee>).take(10).toList();
            final roleMap = {for (final r in roles as List<Role>) r.id: r};
            _selectedDepartingId ??= teamEmps.first.id;

            final departing = teamEmps.firstWhere((e) => e.id == _selectedDepartingId, orElse: () => teamEmps.first);
            final role = roleMap[departing.roleId];
            final candidates = role != null
                ? _replacementUc.call(departing: departing, allEmployees: teamEmps, role: role, allSkills: skills as List<Skill>)
                : [];

            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                DropdownButtonFormField<String>(
                  value: _selectedDepartingId,
                  decoration: const InputDecoration(labelText: 'Departing Employee', prefixIcon: Icon(Icons.person_remove_outlined)),
                  items: teamEmps.map((e) => DropdownMenuItem(value: e.id, child: Text('${e.name} (${e.currentRole})'))).toList(),
                  onChanged: (v) => setState(() => _selectedDepartingId = v),
                ),
                const SizedBox(height: 20),
                if (role != null) ...[
                  Text('Replacement Candidates for "${role.title}"',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                ],
                if (candidates.isEmpty)
                  const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('No candidates found.')))
                else
                  ...candidates.take(5).map((c) => _CandidateCard(
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

class _CandidateCard extends StatelessWidget {
  final dynamic candidate;
  final int rank;
  const _CandidateCard({required this.candidate, required this.rank});

  @override
  Widget build(BuildContext context) {
    final color = candidate.fitScore >= 75 ? AppColors.success : candidate.fitScore >= 50 ? AppColors.warning : AppColors.riskHigh;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(width: 32, height: 32, alignment: Alignment.center, decoration: BoxDecoration(color: AppColors.primary.withOpacity(0.12), borderRadius: BorderRadius.circular(8)), child: Text('#$rank', style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary))),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(candidate.employee.name, style: const TextStyle(fontWeight: FontWeight.bold)),
              Text(candidate.employee.currentRole, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ])),
            Text('${candidate.fitScore}%', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
          ]),
          const SizedBox(height: 10),
          LinearProgressIndicator(value: candidate.fitScore / 100, backgroundColor: color.withOpacity(0.15), valueColor: AlwaysStoppedAnimation<Color>(color), minHeight: 6),
          const SizedBox(height: 10),
          Wrap(spacing: 6, runSpacing: 4, children: [
            ...candidate.matchingSkills.take(3).map((s) => _Tag(label: s.name, color: AppColors.success)),
            ...candidate.missingSkills.take(2).map((s) => _Tag(label: s.name, color: AppColors.riskHigh, dash: true)),
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
      decoration: BoxDecoration(color: color.withOpacity(0.12), borderRadius: BorderRadius.circular(12), border: dash ? Border.all(color: color.withOpacity(0.4), style: BorderStyle.solid) : null),
      child: Text('${dash ? '- ' : '+ '}$label', style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
