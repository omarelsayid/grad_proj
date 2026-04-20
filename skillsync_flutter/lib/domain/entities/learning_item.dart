// lib/domain/entities/learning_item.dart

enum LearningType { course, article, certification, project, mentorship }

class LearningItem {
  final String id;
  final String title;
  final String description;
  final String skillId;
  final LearningType type;
  final String duration;
  final int estimatedHours; // 0 for articles (quick reads)
  final int priority; // 1 = highest
  final String url;
  final String platform;

  const LearningItem({
    required this.id,
    required this.title,
    required this.description,
    required this.skillId,
    required this.type,
    required this.duration,
    required this.estimatedHours,
    required this.priority,
    required this.url,
    required this.platform,
  });

  LearningItem copyWith({
    String? id,
    String? title,
    String? description,
    String? skillId,
    LearningType? type,
    String? duration,
    int? estimatedHours,
    int? priority,
    String? url,
    String? platform,
  }) =>
      LearningItem(
        id: id ?? this.id,
        title: title ?? this.title,
        description: description ?? this.description,
        skillId: skillId ?? this.skillId,
        type: type ?? this.type,
        duration: duration ?? this.duration,
        estimatedHours: estimatedHours ?? this.estimatedHours,
        priority: priority ?? this.priority,
        url: url ?? this.url,
        platform: platform ?? this.platform,
      );

  String get typeLabel {
    switch (type) {
      case LearningType.course:        return 'Course';
      case LearningType.article:       return 'Article';
      case LearningType.certification: return 'Cert';
      case LearningType.project:       return 'Project';
      case LearningType.mentorship:    return 'Mentorship';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is LearningItem && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
