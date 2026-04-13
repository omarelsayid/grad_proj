// lib/domain/entities/payroll_record.dart

enum PayrollStatus { pending, processed, paid }

class PayrollRecord {
  final String id;
  final String employeeId;
  final int month;
  final int year;
  final double basicSalary;
  final double allowances;
  final double deductions;
  final PayrollStatus status;

  const PayrollRecord({
    required this.id,
    required this.employeeId,
    required this.month,
    required this.year,
    required this.basicSalary,
    required this.allowances,
    required this.deductions,
    required this.status,
  });

  double get netSalary => basicSalary + allowances - deductions;

  PayrollRecord copyWith({
    String? id,
    String? employeeId,
    int? month,
    int? year,
    double? basicSalary,
    double? allowances,
    double? deductions,
    PayrollStatus? status,
  }) =>
      PayrollRecord(
        id: id ?? this.id,
        employeeId: employeeId ?? this.employeeId,
        month: month ?? this.month,
        year: year ?? this.year,
        basicSalary: basicSalary ?? this.basicSalary,
        allowances: allowances ?? this.allowances,
        deductions: deductions ?? this.deductions,
        status: status ?? this.status,
      );

  String get statusLabel {
    switch (status) {
      case PayrollStatus.pending: return 'Pending';
      case PayrollStatus.processed: return 'Processed';
      case PayrollStatus.paid: return 'Paid';
    }
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is PayrollRecord && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
