import 'package:flutter/material.dart';

import '../design_system/app_colors.dart';
import '../design_system/app_radius.dart';

class LostifyOutlinedButton extends StatelessWidget {
  const LostifyOutlinedButton({
    super.key,
    required this.onPressed,
    required this.label,
    this.icon,
    this.loading = false,
    this.disabled = false,
    this.width,
  });

  final VoidCallback? onPressed;
  final String label;
  final IconData? icon;
  final bool loading;
  final bool disabled;
  final double? width;

  @override
  Widget build(BuildContext context) {
    final child = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (loading)
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
            ),
          )
        else if (icon != null)
          Icon(icon, size: 18, color: AppColors.primary)
        else
          const SizedBox.shrink(),
        if ((loading || icon != null)) const SizedBox(width: 8),
        Text(label, style: const TextStyle(color: AppColors.primary)),
      ],
    );

    return SizedBox(
      width: width,
      child: OutlinedButton(
        onPressed: disabled || loading ? null : onPressed,
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          side: const BorderSide(color: AppColors.border),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.l),
          ),
        ),
        child: child,
      ),
    );
  }
}
