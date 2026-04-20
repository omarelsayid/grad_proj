// lib/domain/entities/learning_progress.dart

enum LearningStatus { notStarted, inProgress, completed }

extension LearningStatusX on LearningStatus {
  String get label {
    switch (this) {
      case LearningStatus.notStarted: return 'Not Started';
      case LearningStatus.inProgress: return 'In Progress';
      case LearningStatus.completed:  return 'Completed';
    }
  }

  LearningStatus get next =>
      LearningStatus.values[(index + 1) % LearningStatus.values.length];
}
