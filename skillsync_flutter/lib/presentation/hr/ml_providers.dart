// lib/presentation/hr/ml_providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/mock/mock_attendance.dart';
import '../../data/mock/mock_static_data.dart';
import '../../domain/entities/attendance_record.dart';
import '../../domain/entities/turnover_risk_data.dart';
import '../../domain/usecases/calculate_role_fit_use_case.dart';
import '../../services/api_client.dart';
import '../employee/dashboard/provider.dart';

class MlTurnoverEntry {
  final String employeeId;
  final double riskScore;
  final RiskLevel riskLevel;
  final List<String> topFactors;

  const MlTurnoverEntry({
    required this.employeeId,
    required this.riskScore,
    required this.riskLevel,
    required this.topFactors,
  });
}

const _rfUc = CalculateRoleFitUseCase();

/// Fetches ML-powered turnover risk for all employees in parallel.
/// Returns empty map if ML service is unavailable (graceful fallback).
final mlTurnoverProvider = FutureProvider<Map<String, MlTurnoverEntry>>((ref) async {
  final emps = await ref.watch(allEmployeesProvider.future);
  final roles = await ref.watch(employeeRolesProvider.future);
  final roleMap = {for (final r in roles) r.id: r};

  final entries = await Future.wait(
    emps.map((emp) async {
      final role = roleMap[emp.roleId];
      final roleFit = role != null ? _rfUc.call(emp, role).fitScore.toDouble() : 50.0;
      final commuteKm = switch (emp.commuteDistance) {
        'near'     => 5.0,
        'moderate' => 20.0,
        'far'      => 40.0,
        _          => 10.0,
      };
      final tenureDays = DateTime.now().difference(emp.joinDate).inDays;
      final attendance = generateAttendance(emp.id);
      final absences = attendance.where((a) => a.status == AttendanceStatus.absent).length;
      final absenceRate = attendance.isNotEmpty ? absences / attendance.length : 0.0;
      final lateCount = attendance.where((a) => a.status == AttendanceStatus.late).length;
      final leaveCount = mockLeaveRequests.where((l) => l.employeeId == emp.id).length;
      final attendanceStatus = absenceRate > 0.2 ? 'critical' : absenceRate > 0.1 ? 'at_risk' : 'normal';

      try {
        final data = await ApiClient.instance.getMlTurnoverRisk({
          'employee_id': emp.id,
          'commute_distance_km': commuteKm,
          'tenure_days': tenureDays,
          'role_fit_score': roleFit,
          'absence_rate': absenceRate,
          'late_arrivals_30d': lateCount,
          'leave_requests_90d': leaveCount,
          'satisfaction_score': emp.satisfactionScore.clamp(0.0, 100.0),
          'attendance_status': attendanceStatus,
        });

        RiskLevel parseLevel(String s) => switch (s) {
          'critical' => RiskLevel.critical,
          'high'     => RiskLevel.high,
          'medium'   => RiskLevel.medium,
          _          => RiskLevel.low,
        };

        return MapEntry(emp.id, MlTurnoverEntry(
          employeeId: emp.id,
          riskScore:  (data['risk_score'] as num).toDouble(),
          riskLevel:  parseLevel(data['risk_level'] as String? ?? 'low'),
          topFactors: (data['top_factors'] as List<dynamic>? ?? []).cast<String>(),
        ));
      } catch (_) {
        return null;
      }
    }),
  );

  return Map.fromEntries(entries.whereType<MapEntry<String, MlTurnoverEntry>>());
});

/// Fetches ML org-wide skill gap analysis from Python service.
/// Returns null if ML service is unavailable.
final mlSkillGapsProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  try {
    return await ApiClient.instance.getMlSkillGaps();
  } catch (_) {
    return null;
  }
});
