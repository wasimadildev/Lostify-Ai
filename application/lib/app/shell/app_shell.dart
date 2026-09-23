import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/design_system/app_colors.dart';
import '../../core/design_system/app_radius.dart';
import '../../core/design_system/app_spacing.dart';
import '../../core/widgets/lostify_bottom_nav.dart';

class LostifyAppShell extends StatelessWidget {
  const LostifyAppShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  void _onDestinationSelected(BuildContext context, int index) {
    if (index == 2) {
      context.push('/report');
      return;
    }

    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const _LostifyNavigationDrawer(),
      body: navigationShell,
      bottomNavigationBar: LostifyBottomNavigation(
        currentIndex: navigationShell.currentIndex,
        onTap: (index) => _onDestinationSelected(context, index),
      ),
    );
  }
}

class _LostifyNavigationDrawer extends StatelessWidget {
  const _LostifyNavigationDrawer();

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: AppColors.surface,
      child: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: const BoxDecoration(
                    gradient: AppColors.brandGradient,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.location_on_rounded, color: Colors.white),
                ),
                const SizedBox(width: AppSpacing.md),
                Text('Lostify AI', style: Theme.of(context).textTheme.titleLarge),
              ],
            ),
            const SizedBox(height: AppSpacing.xxl),
            const _DrawerSectionLabel('Workspace'),
            _DrawerDestination(
              icon: Icons.home_rounded,
              label: 'Home',
              onTap: () => _goTo(context, '/home'),
            ),
            _DrawerDestination(
              icon: Icons.search_rounded,
              label: 'Search',
              onTap: () => _goTo(context, '/search'),
            ),
            _DrawerDestination(
              icon: Icons.notifications_none_rounded,
              label: 'Alerts',
              onTap: () => _goTo(context, '/alerts'),
            ),
            const SizedBox(height: AppSpacing.lg),
            const _DrawerSectionLabel('Account'),
            _DrawerDestination(
              icon: Icons.person_outline_rounded,
              label: 'Profile',
              onTap: () => _goTo(context, '/profile'),
            ),
            _DrawerDestination(
              icon: Icons.groups_outlined,
              label: 'Communities',
              onTap: () => _goTo(context, '/communities'),
            ),
            _DrawerDestination(
              icon: Icons.settings_outlined,
              label: 'Settings',
              onTap: () => _goTo(context, '/settings'),
            ),
          ],
        ),
      ),
    );
  }

  void _goTo(BuildContext context, String location) {
    Navigator.of(context).pop();
    context.go(location);
  }
}

class _DrawerSectionLabel extends StatelessWidget {
  const _DrawerSectionLabel(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.textTertiary,
              letterSpacing: 0.8,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}

class _DrawerDestination extends StatelessWidget {
  const _DrawerDestination({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.m)),
      leading: Icon(icon, color: AppColors.textSecondary),
      title: Text(label),
      onTap: onTap,
    );
  }
}