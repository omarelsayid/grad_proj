// lib/domain/entities/resignation_request.dart

enum ResignationStatus { pending, approved, rejected }

class ResignationRequest {
  final String id;
  final String employeeId;
  final DateTime lastWorkingDate;
  final int noticePeriodDays;
  final String reason;
  final ResignationStatus status;
  final DateTime submittedAt;

  const ResignationRequest({
    required this.id,
    required this.employeeId,
    required this.lastWorkingDate,
    required this.noticePeriodDays,
    required this.reason,
    required this.status,
    required this.submittedAt,
  });

  ResignationRequest copyWith({
    String? id,
    String? employeeId,
    DateTime? lastWorkingDate,
    int? noticePeriodDays,
    String? reason,
    ResignationStatus? status,
    DateTime? submittedAt,
  }) =>
      ResignationRequest(
        id: id ?? this.id,
        employeeId: employeeId ?? this.employeeId,
        lastWorkingDate: lastWorkingDate ?? this.lastWorkingDate,
        noticePeriodDays: noticePeriodDays ?? this.noticePeriodDays,
        reason: reason ?? this.reason,
        status: status ?? this.status,
        submittedAt: submittedAt ?? this.submittedAt,
      );

  String get statusLabel {
    switch (status) {
      case ResignationStatus.pending: return 'Pending';
      case ResignationStatus.approved: return 'Approved';
      case ResignationStatus.rejected: return 'Rejected';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ResignationRequest && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
