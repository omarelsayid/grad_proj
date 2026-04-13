// lib/domain/entities/turnover_risk_data.dart
import 'employee.dart';

enum RiskLevel { low, medium, high, critical }

class TurnoverFactorBreakdown {
  final String factor;
  final double score;
  final double maxScore;
  final bool triggered;

  const TurnoverFactorBreakdown({
    required this.factor,
    required this.score,
    required this.maxScore,
    required this.triggered,
  });
}

class TurnoverRiskData {
  final Employee employee;
  final double riskScore;
  final RiskLevel riskLevel;
  final List<TurnoverFactorBreakdown> factorBreakdown;

  const TurnoverRiskData({
    required this.employee,
    required this.riskScore,
    required this.riskLevel,
    required this.factorBreakdown,
  });

  String get riskLevelLabel {
    switch (riskLevel) {
      case RiskLevel.low: return 'Low';
      case RiskLevel.medium: return 'Medium';
      case RiskLevel.high: return 'High';
      case RiskLevel.critical: return 'Critical';
    }
  }
}
