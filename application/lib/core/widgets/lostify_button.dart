import 'package:flutter/material.dart';

import '../design_system/app_colors.dart';
import '../design_system/app_radius.dart';
import '../design_system/app_spacing.dart';

class LostifyButton extends StatelessWidget {
  const LostifyButton({
    super.key,
    required this.onPressed,
    required this.label,
    this.icon,
    this.isPrimary = true,
    this.loading = false,
    this.disabled = false,
    this.width,
  });

  final VoidCallback? onPressed;
  final String label;
  final IconData? icon;
  final bool isPrimary;
  final bool loading;
  final bool disabled;
  final double? width;

  @override
  Widget build(BuildContext context) {
    final buttonStyle = isPrimary
        ? FilledButton.styleFrom(
            backgroundColor: AppColors.primary,
            foregroundColor: AppColors.onPrimary,
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl, vertical: AppSpacing.lg),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadius.l),
            ),
          )
        : OutlinedButton.styleFrom(
            foregroundColor: AppColors.textPrimary,
            side: const BorderSide(color: AppColors.border),
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl, vertical: AppSpacing.lg),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadius.l),
            ),
          );

    final child = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (loading)
          const SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.onPrimary),
          )
        else if (icon != null)
          Icon(icon, size: 18),
        if ((loading || icon != null)) const SizedBox(width: AppSpacing.sm),
        Text(label),
      ],
    );

    return SizedBox(
      width: width,
      child: isPrimary
          ? FilledButton(
              onPressed: disabled || loading ? null : onPressed,
              style: buttonStyle,
              child: child,
            )
          : OutlinedButton(
              onPressed: disabled || loading ? null : onPressed,
              style: buttonStyle,
              child: child,
            ),
    );
  }
}
