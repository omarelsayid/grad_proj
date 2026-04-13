// lib/data/mock/mock_attendance.dart
import '../../domain/entities/attendance_record.dart';

List<AttendanceRecord> generateAttendance(String employeeId) {
  final statuses = [
    AttendanceStatus.present, AttendanceStatus.present,
    AttendanceStatus.present, AttendanceStatus.late,
    AttendanceStatus.present, AttendanceStatus.remote,
    AttendanceStatus.absent, AttendanceStatus.present,
    AttendanceStatus.present, AttendanceStatus.present,
    AttendanceStatus.halfDay, AttendanceStatus.present,
    AttendanceStatus.present, AttendanceStatus.late,
    AttendanceStatus.present, AttendanceStatus.present,
    AttendanceStatus.remote, AttendanceStatus.present,
    AttendanceStatus.absent, AttendanceStatus.present,
    AttendanceStatus.present, AttendanceStatus.present,
  ];

  final records = <AttendanceRecord>[];
  final base = DateTime(2026, 3, 1);
  int statusIdx = 0;

  for (int i = 0; i < 30; i++) {
    final date = base.add(Duration(days: i));
    if (date.weekday == DateTime.friday || date.weekday == DateTime.saturday) {
      continue;
    }
    final status = statuses[statusIdx % statuses.length];
    statusIdx++;
    final checkIn = status != AttendanceStatus.absent
        ? DateTime(date.year, date.month, date.day,
            status == AttendanceStatus.late ? 10 : 9, 0)
        : null;
    final checkOut = checkIn != null
        ? checkIn.add(Duration(hours: status == AttendanceStatus.halfDay ? 4 : 8))
        : null;

    records.add(AttendanceRecord(
      id: '${employeeId}_att_$i',
      employeeId: employeeId,
      date: date,
      checkIn: checkIn,
      checkOut: checkOut,
      status: status,
      type: 'regular',
    ));
  }
  return records;
}
