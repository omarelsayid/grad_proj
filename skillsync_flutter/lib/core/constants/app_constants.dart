// lib/core/constants/app_constants.dart

class AppConstants {
  AppConstants._();

  static const String appName = 'SkillSync HRMS';
  static const String version = '1.0.0';

  // Route names
  static const String routeAuth = '/auth';
  static const String routeEmployee = '/employee';
  static const String routeManager = '/manager';
  static const String routeHr = '/hr';

  // Proficiency labels
  static const List<String> proficiencyLabels = [
    'None', 'Beginner', 'Basic', 'Intermediate', 'Advanced', 'Expert',
  ];

  // Leave types
  static const String leaveAnnual = 'annual';
  static const String leaveSick = 'sick';
  static const String leaveCompassionate = 'compassionate';

  // Risk levels
  static const String riskLow = 'low';
  static const String riskMedium = 'medium';
  static const String riskHigh = 'high';
  static const String riskCritical = 'critical';

  // Leave balances
  static const int annualLeaveTotal = 21;
  static const int sickLeaveTotal = 10;
  static const int compassionateLeaveTotal = 5;

  // AI Chat responses pool
  static const List<String> aiResponses = [
    'According to company policy, annual leave must be requested at least 3 days in advance.',
    'Your leave balance resets every January 1st. Unused sick leave is not carried over.',
    'For payroll inquiries, please contact HR at hr@skillsync.dev.',
    'The performance review cycle runs quarterly. Your next review is scheduled for Q3.',
    'To update your personal information, visit the Settings section of your profile.',
    'Training reimbursements require prior approval. Submit your request via the Learning section.',
    'Remote work policy allows up to 2 days per week for eligible roles. Check your role details.',
    'Overtime is compensated at 1.5x your hourly rate for weekdays and 2x for public holidays.',
  ];
}
