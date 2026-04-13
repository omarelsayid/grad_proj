// lib/core/widgets/proficiency_bar.dart
import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../constants/app_constants.dart';

class ProficiencyBar extends StatelessWidget {
  final int proficiency; // 0-5
  final bool showLabel;
  final double height;

  const ProficiencyBar({
    super.key,
    required this.proficiency,
    this.showLabel = true,
    this.height = 8,
  });

  @override
  Widget build(BuildContext context) {
    final pct = proficiency / 5.0;
    final color = pct < 0.4
        ? AppColors.riskHigh
        : pct < 0.7
            ? AppColors.warning
            : AppColors.success;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (showLabel)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                AppConstants.proficiencyLabels[proficiency.clamp(0, 5)],
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
              ),
              Text(
                '$proficiency/5',
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
        if (showLabel) const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(height),
          child: LinearProgressIndicator(
            value: pct,
            minHeight: height,
            backgroundColor: Colors.grey.withOpacity(0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ],
    );
  }
}
