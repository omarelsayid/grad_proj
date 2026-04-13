// lib/domain/entities/leave_request.dart

enum LeaveStatus { pending, approved, rejected }

class LeaveRequest {
  final String id;
  final String employeeId;
  final String leaveType; // annual | sick | compassionate
  final DateTime startDate;
  final DateTime endDate;
  final String reason;
  final LeaveStatus status;

  const LeaveRequest({
    required this.id,
    required this.employeeId,
    required this.leaveType,
    required this.startDate,
    required this.endDate,
    required this.reason,
    required this.status,
  });

  int get durationDays => endDate.difference(startDate).inDays + 1;

  LeaveRequest copyWith({
    String? id,
    String? employeeId,
    String? leaveType,
    DateTime? startDate,
    DateTime? endDate,
    String? reason,
    LeaveStatus? status,
  }) =>
      LeaveRequest(
        id: id ?? this.id,
        employeeId: employeeId ?? this.employeeId,
        leaveType: leaveType ?? this.leaveType,
        startDate: startDate ?? this.startDate,
        endDate: endDate ?? this.endDate,
        reason: reason ?? this.reason,
        status: status ?? this.status,
      );

  String get statusLabel {
    switch (status) {
      case LeaveStatus.pending: return 'Pending';
      case LeaveStatus.approved: return 'Approved';
      case LeaveStatus.rejected: return 'Rejected';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is LeaveRequest && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
