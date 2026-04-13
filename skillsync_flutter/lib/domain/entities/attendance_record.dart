// lib/domain/entities/attendance_record.dart

enum AttendanceStatus { present, absent, late, halfDay, remote }

class AttendanceRecord {
  final String id;
  final String employeeId;
  final DateTime date;
  final DateTime? checkIn;
  final DateTime? checkOut;
  final AttendanceStatus status;
  final String type;

  const AttendanceRecord({
    required this.id,
    required this.employeeId,
    required this.date,
    this.checkIn,
    this.checkOut,
    required this.status,
    required this.type,
  });

  AttendanceRecord copyWith({
    String? id,
    String? employeeId,
    DateTime? date,
    DateTime? checkIn,
    DateTime? checkOut,
    AttendanceStatus? status,
    String? type,
  }) =>
      AttendanceRecord(
        id: id ?? this.id,
        employeeId: employeeId ?? this.employeeId,
        date: date ?? this.date,
        checkIn: checkIn ?? this.checkIn,
        checkOut: checkOut ?? this.checkOut,
        status: status ?? this.status,
        type: type ?? this.type,
      );

  String get statusLabel {
    switch (status) {
      case AttendanceStatus.present: return 'Present';
      case AttendanceStatus.absent: return 'Absent';
      case AttendanceStatus.late: return 'Late';
      case AttendanceStatus.halfDay: return 'Half Day';
      case AttendanceStatus.remote: return 'Remote';
    }
  }

  Duration? get hoursWorked {
    if (checkIn == null || checkOut == null) return null;
    return checkOut!.difference(checkIn!);
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is AttendanceRecord && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
