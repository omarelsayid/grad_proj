// lib/core/widgets/status_chip.dart
import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class StatusChip extends StatelessWidget {
  final String label;
  final Color color;

  const StatusChip({super.key, required this.label, required this.color});

  factory StatusChip.fromStatus(String status) {
    final color = switch (status.toLowerCase()) {
      'approved' || 'present' || 'paid' || 'active' => AppColors.success,
      'pending' || 'late' || 'processed' => AppColors.warning,
      'rejected' || 'absent' => AppColors.error,
      'remote' => AppColors.info,
      'half_day' || 'halfday' => Colors.purple,
      _ => Colors.grey,
    };
    return StatusChip(label: _capitalize(status), color: color);
  }

  static String _capitalize(String s) {
    if (s.isEmpty) return s;
    return s[0].toUpperCase() + s.substring(1).toLowerCase().replaceAll('_', ' ');
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
