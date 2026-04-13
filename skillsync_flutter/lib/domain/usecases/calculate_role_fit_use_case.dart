// lib/domain/usecases/calculate_role_fit_use_case.dart
import '../entities/employee.dart';
import '../entities/role.dart';

class RoleFitResult {
  final int fitScore; // 0-100
  final List<String> matchingSkillIds;
  final List<String> missingSkillIds;

  const RoleFitResult({
    required this.fitScore,
    required this.matchingSkillIds,
    required this.missingSkillIds,
  });
}

class CalculateRoleFitUseCase {
  const CalculateRoleFitUseCase();

  RoleFitResult call(Employee employee, Role role) {
    if (role.requiredSkills.isEmpty) {
      return const RoleFitResult(
        fitScore: 100,
        matchingSkillIds: [],
        missingSkillIds: [],
      );
    }

    final employeeSkillMap = {
      for (final es in employee.skills) es.skillId: es.proficiency,
    };

    double totalScore = 0;
    double maxScore = 0;
    final matching = <String>[];
    final missing = <String>[];

    for (final req in role.requiredSkills) {
      final actual = employeeSkillMap[req.skillId] ?? 0;
      final contribution = actual.clamp(0, req.minProficiency).toDouble();
      totalScore += contribution;
      maxScore += req.minProficiency.toDouble();

      if (actual >= req.minProficiency) {
        matching.add(req.skillId);
      } else {
        missing.add(req.skillId);
      }
    }

    final score = maxScore > 0
        ? ((totalScore / maxScore) * 100).round().clamp(0, 100)
        : 100;

    return RoleFitResult(
      fitScore: score,
      matchingSkillIds: matching,
      missingSkillIds: missing,
    );
  }
}
