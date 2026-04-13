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
    int limit = 10,
  }) {
    final result = _roleFitUseCase.call(employee, targetRole);
    final missingSkillIds = result.missingSkillIds.toSet();

    final relevant = catalog
        .where((item) => missingSkillIds.contains(item.skillId))
        .toList()
      ..sort((a, b) => a.priority.compareTo(b.priority));

    return relevant.take(limit).toList();
  }
}
