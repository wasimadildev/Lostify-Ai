import 'package:flutter/material.dart';

class LostifySectionHeader extends StatelessWidget {
  const LostifySectionHeader({
    super.key,
    required this.title,
    this.action,
    this.trailing,
  });

  final String title;
  final String? action;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const Spacer(),
        action != null
            ? TextButton(
                onPressed: () {},
                child: Text(action!),
              )
            : trailing ?? const SizedBox.shrink(),
      ],
    );
  }
}
