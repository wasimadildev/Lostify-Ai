import 'package:flutter/material.dart';

import '../design_system/app_colors.dart';
import '../design_system/app_radius.dart';

class LostifySearchBar extends StatelessWidget {
  const LostifySearchBar({
    super.key,
    this.hintText,
    this.onTap,
    this.controller,
    this.onChanged,
  });

  final String? hintText;
  final VoidCallback? onTap;
  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.xl),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          const Icon(Icons.search_rounded, color: AppColors.textSecondary),
          const SizedBox(width: 12),
          Expanded(
            child: TextField(
              controller: controller,
              onTap: onTap,
              onChanged: onChanged,
              readOnly: onTap != null,
              decoration: InputDecoration(
                isDense: true,
                border: InputBorder.none,
                hintText: hintText ?? 'Search',
                hintStyle: const TextStyle(color: AppColors.textSecondary),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
