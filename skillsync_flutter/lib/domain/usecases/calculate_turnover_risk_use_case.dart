// lib/domain/usecases/calculate_turnover_risk_use_case.dart
import '../entities/employee.dart';
import '../entities/attendance_record.dart';
import '../entities/leave_request.dart';
import '../entities/turnover_risk_data.dart';
import 'calculate_role_fit_use_case.dart';
import '../entities/role.dart';

class CalculateTurnoverRiskUseCase {
  final CalculateRoleFitUseCase _roleFitUseCase;

  const CalculateTurnoverRiskUseCase(this._roleFitUseCase);

  TurnoverRiskData call(
    Employee employee,
    Role? role,
    List<AttendanceRecord> attendance,
    List<LeaveRequest> leaves,
  ) {
    final factors = <TurnoverFactorBreakdown>[];
    double total = 0;

    // Commute distance (max 45)
    final commuteScore = _commuteScore(employee.commuteDistance);
    factors.add(TurnoverFactorBreakdown(
      factor: 'Commute Distance',
      score: commuteScore,
      maxScore: 45,
      triggered: commuteScore > 0,
    ));
    total += commuteScore;

    // Tenure < 1 year (max 35)
    final tenureScore = employee.tenureYears < 1 ? 35.0 : 0.0;
    factors.add(TurnoverFactorBreakdown(
      factor: 'Short Tenure (<1yr)',
      score: tenureScore,
      maxScore: 35,
      triggered: tenureScore > 0,
    ));
    total += tenureScore;

    // Role fit < 60% (max 15)
    double roleFitScore = 0;
    if (role != null) {
      final fit = _roleFitUseCase.call(employee, role).fitScore;
      roleFitScore = fit < 60 ? 15.0 : 0.0;
    }
    factors.add(TurnoverFactorBreakdown(
      factor: 'Low Role Fit (<60%)',
      score: roleFitScore,
      maxScore: 15,
      triggered: roleFitScore > 0,
    ));
    total += roleFitScore;

    // Absence rate >= 15% (max 20)
    final absenceRate = _absenceRate(attendance);
    final absenceScore = absenceRate >= 0.15 ? 20.0 : 0.0;
    factors.add(TurnoverFactorBreakdown(
      factor: 'High Absence Rate (>=15%)',
      score: absenceScore,
      maxScore: 20,
      triggered: absenceScore > 0,
    ));
    total += absenceScore;

    // Late arrivals >= 6 (max 8)
    final lateCount = attendance.where((a) => a.status == AttendanceStatus.late).length;
    final lateScore = lateCount >= 6 ? 8.0 : 0.0;
    factors.add(TurnoverFactorBreakdown(
      factor: 'Frequent Late Arrivals (>=6)',
      score: lateScore,
      maxScore: 8,
      triggered: lateScore > 0,
    ));
    total += lateScore;

    // Satisfaction < 65 (max 12)
    final satisfactionScore = employee.satisfactionScore < 65 ? 12.0 : 0.0;
    factors.add(TurnoverFactorBreakdown(
      factor: 'Low Satisfaction (<65)',
      score: satisfactionScore,
      maxScore: 12,
      triggered: satisfactionScore > 0,
    ));
    total += satisfactionScore;

    // Leave requests >= 5 (max 10)
    final leaveScore = leaves.length >= 5 ? 10.0 : 0.0;
    factors.add(TurnoverFactorBreakdown(
      factor: 'Many Leave Requests (>=5)',
      score: leaveScore,
      maxScore: 10,
      triggered: leaveScore > 0,
    ));
    total += leaveScore;

    return TurnoverRiskData(
      employee: employee,
      riskScore: total,
      riskLevel: _bucket(total),
      factorBreakdown: factors,
    );
  }

  double _commuteScore(String distance) {
    switch (distance) {
      case 'very_far': return 45;
      case 'far': return 25;
      case 'moderate': return 10;
      default: return 0;
    }
  }

  double _absenceRate(List<AttendanceRecord> attendance) {
    if (attendance.isEmpty) return 0;
    final absences = attendance.where((a) => a.status == AttendanceStatus.absent).length;
    return absences / attendance.length;
  }

  RiskLevel _bucket(double score) {
    if (score < 30) return RiskLevel.low;
    if (score < 60) return RiskLevel.medium;
    if (score < 90) return RiskLevel.high;
    return RiskLevel.critical;
  }
}
