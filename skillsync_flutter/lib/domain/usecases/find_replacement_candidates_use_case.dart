// lib/domain/usecases/find_replacement_candidates_use_case.dart
import '../entities/employee.dart';
import '../entities/role.dart';
import '../entities/skill.dart';
import 'calculate_role_fit_use_case.dart';

class ReplacementCandidate {
  final Employee employee;
  final int fitScore;
  final List<Skill> matchingSkills;
  final List<Skill> missingSkills;

  const ReplacementCandidate({
    required this.employee,
    required this.fitScore,
    required this.matchingSkills,
    required this.missingSkills,
  });
}

class FindReplacementCandidatesUseCase {
  final CalculateRoleFitUseCase _roleFitUseCase;

  const FindReplacementCandidatesUseCase(this._roleFitUseCase);

  List<ReplacementCandidate> call({
    required Employee departing,
    required List<Employee> allEmployees,
    required Role role,
    required List<Skill> allSkills,
    int limit = 10,
  }) {
    final skillMap = {for (final s in allSkills) s.id: s};

    final candidates = allEmployees
        .where((e) => e.id != departing.id)
        .map((employee) {
          final result = _roleFitUseCase.call(employee, role);
          return ReplacementCandidate(
            employee: employee,
            fitScore: result.fitScore,
            matchingSkills: result.matchingSkillIds
                .map((id) => skillMap[id])
                .whereType<Skill>()
                .toList(),
            missingSkills: result.missingSkillIds
                .map((id) => skillMap[id])
                .whereType<Skill>()
                .toList(),
          );
        })
        .toList()
      ..sort((a, b) => b.fitScore.compareTo(a.fitScore));

    return candidates.take(limit).toList();
  }
}
