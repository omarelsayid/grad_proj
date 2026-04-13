// lib/domain/entities/todo.dart

enum TodoPriority { low, medium, high }

class Todo {
  final String id;
  final String title;
  final String description;
  final DateTime dueDate;
  final TodoPriority priority;
  final bool completed;
  final String employeeId;

  const Todo({
    required this.id,
    required this.title,
    required this.description,
    required this.dueDate,
    required this.priority,
    required this.completed,
    required this.employeeId,
  });

  Todo copyWith({
    String? id,
    String? title,
    String? description,
    DateTime? dueDate,
    TodoPriority? priority,
    bool? completed,
    String? employeeId,
  }) =>
      Todo(
        id: id ?? this.id,
        title: title ?? this.title,
        description: description ?? this.description,
        dueDate: dueDate ?? this.dueDate,
        priority: priority ?? this.priority,
        completed: completed ?? this.completed,
        employeeId: employeeId ?? this.employeeId,
      );

  String get priorityLabel {
    switch (priority) {
      case TodoPriority.low: return 'Low';
      case TodoPriority.medium: return 'Medium';
      case TodoPriority.high: return 'High';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Todo && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
