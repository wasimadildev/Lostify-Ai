import 'package:flutter/material.dart';

import '../design_system/app_spacing.dart';

class LostifyAppBar extends StatelessWidget implements PreferredSizeWidget {
  const LostifyAppBar({
    super.key,
    this.title,
    this.leading,
    this.trailing,
    this.centerTitle = true,
  });

  final String? title;
  final Widget? leading;
  final Widget? trailing;
  final bool centerTitle;

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight + 8);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      automaticallyImplyLeading: false,
      backgroundColor: Colors.transparent,
      elevation: 0,
      titleSpacing: AppSpacing.lg,
      leading: leading,
      title: title != null
          ? Text(
              title!,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            )
          : null,
      centerTitle: centerTitle,
      actions: trailing != null ? [Padding(padding: const EdgeInsets.only(right: 16), child: trailing)] : null,
    );
  }
}
