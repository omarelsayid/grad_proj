// lib/domain/entities/learning_item.dart

enum LearningType { course, certification, project, mentorship }

class LearningItem {
  final String id;
  final String title;
  final String description;
  final String skillId;
  final LearningType type;
  final String duration;
  final int priority; // 1 = highest
  final String url;

  const LearningItem({
    required this.id,
    required this.title,
    required this.description,
    required this.skillId,
    required this.type,
    required this.duration,
    required this.priority,
    required this.url,
  });

  LearningItem copyWith({
    String? id,
    String? title,
    String? description,
    String? skillId,
    LearningType? type,
    String? duration,
    int? priority,
    String? url,
  }) =>
      LearningItem(
        id: id ?? this.id,
        title: title ?? this.title,
        description: description ?? this.description,
        skillId: skillId ?? this.skillId,
        type: type ?? this.type,
        duration: duration ?? this.duration,
        priority: priority ?? this.priority,
        url: url ?? this.url,
      );

  String get typeLabel {
    switch (type) {
      case LearningType.course: return 'Course';
      case LearningType.certification: return 'Certification';
      case LearningType.project: return 'Project';
      case LearningType.mentorship: return 'Mentorship';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is LearningItem && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
