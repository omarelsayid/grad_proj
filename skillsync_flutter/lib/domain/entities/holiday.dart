// lib/domain/entities/holiday.dart

enum HolidayType { public, company, optional }

class Holiday {
  final String id;
  final String name;
  final DateTime date;
  final HolidayType type;

  const Holiday({
    required this.id,
    required this.name,
    required this.date,
    required this.type,
  });

  Holiday copyWith({
    String? id,
    String? name,
    DateTime? date,
    HolidayType? type,
  }) =>
      Holiday(
        id: id ?? this.id,
        name: name ?? this.name,
        date: date ?? this.date,
        type: type ?? this.type,
      );

  String get typeLabel {
    switch (type) {
      case HolidayType.public: return 'Public';
      case HolidayType.company: return 'Company';
      case HolidayType.optional: return 'Optional';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Holiday && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
