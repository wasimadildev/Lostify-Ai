import 'package:flutter/material.dart';

import '../design_system/app_colors.dart';

class LostifyStatusBadge extends StatelessWidget {
  const LostifyStatusBadge({
    super.key,
    required this.label,
    this.color,
    this.backgroundColor,
  });

  final String label;
  final Color? color;
  final Color? backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: backgroundColor ?? AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
          color: color ?? AppColors.primary,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
