// lib/core/theme/app_colors.dart
import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  static const Color primary = Color(0xFF1F4E8C);
  static const Color accent = Color(0xFF6CC04A);
  static const Color secondary = Color(0xFF2FA4A9);
  static const Color primaryLight = Color(0xFF3A6CB0);
  static const Color primaryDark = Color(0xFF153666);

  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFF9800);
  static const Color error = Color(0xFFF44336);
  static const Color info = Color(0xFF2196F3);

  static const Color backgroundLight = Color(0xFFF5F7FA);
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color backgroundDark = Color(0xFF121212);
  static const Color surfaceDark = Color(0xFF1E1E1E);

  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textDisabled = Color(0xFFBDBDBD);

  // Risk level colors
  static const Color riskLow = Color(0xFF4CAF50);
  static const Color riskMedium = Color(0xFFFF9800);
  static const Color riskHigh = Color(0xFFF44336);
  static const Color riskCritical = Color(0xFF9C27B0);

  // Skill category colors
  static const Color skillTechnical = Color(0xFF1F4E8C);
  static const Color skillSoft = Color(0xFF6CC04A);
  static const Color skillManagement = Color(0xFF2FA4A9);
  static const Color skillDomain = Color(0xFFFF9800);

  // Attendance status colors
  static const Color attendancePresent = Color(0xFF4CAF50);
  static const Color attendanceAbsent = Color(0xFFF44336);
  static const Color attendanceLate = Color(0xFFFF9800);
  static const Color attendanceHalfDay = Color(0xFF2196F3);
  static const Color attendanceRemote = Color(0xFF9C27B0);
}
