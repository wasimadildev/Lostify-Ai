import 'package:flutter/material.dart';

import '../design_system/app_colors.dart';
import '../design_system/app_radius.dart';
import '../design_system/app_shadows.dart';
import '../design_system/app_spacing.dart';

class LostifyBottomNavigation extends StatelessWidget {
  const LostifyBottomNavigation({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    final items = [
      _NavItem(Icons.home_rounded, 'Home'),
      _NavItem(Icons.search_rounded, 'Search'),
      _NavItem(Icons.add_rounded, 'Create', isCenter: true),
      _NavItem(Icons.notifications_none_rounded, 'Alerts'),
      _NavItem(Icons.person_outline_rounded, 'Profile'),
    ];

    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.lg,
          0,
          AppSpacing.lg,
          AppSpacing.md,
        ),
        child: Container(
          height: 76,
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.sm,
            vertical: AppSpacing.sm,
          ),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(AppRadius.xxl),
            border: Border.all(color: AppColors.border),
            boxShadow: AppShadows.card,
          ),
          child: Row(
            children: List.generate(items.length, (index) {
              final item = items[index];
              final selected = index == currentIndex;

              if (item.isCenter) {
                return Expanded(
                  child: Center(
                    child: Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: AppColors.brandGradient,
                        boxShadow: AppShadows.soft,
                      ),
                      child: IconButton(
                        onPressed: () => onTap(index),
                        icon: Icon(item.icon, color: Colors.white, size: 26),
                        tooltip: item.label,
                      ),
                    ),
                  ),
                );
              }

              return Expanded(
                child: InkWell(
                  onTap: () => onTap(index),
                  borderRadius: BorderRadius.circular(AppRadius.l),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        item.icon,
                        color: selected ? AppColors.primary : AppColors.textSecondary,
                        size: 22,
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        item.label,
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          color: selected ? AppColors.primary : AppColors.textSecondary,
                          fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem(this.icon, this.label, {this.isCenter = false});

  final IconData icon;
  final String label;
  final bool isCenter;
}
