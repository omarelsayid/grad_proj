// lib/domain/entities/leave_balance.dart

class LeaveBalance {
  final String employeeId;
  final int annualTotal;
  final int annualUsed;
  final int sickTotal;
  final int sickUsed;
  final int compassionateTotal;
  final int compassionateUsed;

  const LeaveBalance({
    required this.employeeId,
    required this.annualTotal,
    required this.annualUsed,
    required this.sickTotal,
    required this.sickUsed,
    required this.compassionateTotal,
    required this.compassionateUsed,
  });

  int get annualRemaining => annualTotal - annualUsed;
  int get sickRemaining => sickTotal - sickUsed;
  int get compassionateRemaining => compassionateTotal - compassionateUsed;

  LeaveBalance copyWith({
    String? employeeId,
    int? annualTotal,
    int? annualUsed,
    int? sickTotal,
    int? sickUsed,
    int? compassionateTotal,
    int? compassionateUsed,
  }) =>
      LeaveBalance(
        employeeId: employeeId ?? this.employeeId,
        annualTotal: annualTotal ?? this.annualTotal,
        annualUsed: annualUsed ?? this.annualUsed,
        sickTotal: sickTotal ?? this.sickTotal,
        sickUsed: sickUsed ?? this.sickUsed,
        compassionateTotal: compassionateTotal ?? this.compassionateTotal,
        compassionateUsed: compassionateUsed ?? this.compassionateUsed,
      );
}
