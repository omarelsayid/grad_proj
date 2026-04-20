// lib/domain/usecases/get_suggested_learning_use_case.dart
import '../entities/employee.dart';
import '../entities/role.dart';
import '../entities/learning_item.dart';
import 'calculate_role_fit_use_case.dart';

class GetSuggestedLearningUseCase {
  final CalculateRoleFitUseCase _roleFitUseCase;

  const GetSuggestedLearningUseCase(this._roleFitUseCase);

  List<LearningItem> call({
    required Employee employee,
    required Role targetRole,
    required List<LearningItem> catalog,
    int limit = 15,
  }) {
    final result = _roleFitUseCase.call(employee, targetRole);
    final missingSkillIds = result.missingSkillIds.toSet();
    final employeeSkillIds = {for (final es in employee.skills) es.skillId};

    // 1. Courses that close skill gaps (highest value)
    final gapItems = catalog
        .where((item) => missingSkillIds.contains(item.skillId))
        .toList()
      ..sort((a, b) => a.priority.compareTo(b.priority));

    // 2. Courses for skills the employee already has (level-up / deepen)
    final levelUpItems = catalog
        .where((item) =>
            !missingSkillIds.contains(item.skillId) &&
            employeeSkillIds.contains(item.skillId))
        .toList()
      ..sort((a, b) => a.priority.compareTo(b.priority));

    // 3. Remaining courses (broaden knowledge)
    final otherItems = catalog
        .where((item) =>
            !missingSkillIds.contains(item.skillId) &&
            !employeeSkillIds.contains(item.skillId))
        .toList()
      ..sort((a, b) => a.priority.compareTo(b.priority));

    return [...gapItems, ...levelUpItems, ...otherItems].take(limit).toList();
  }
}
