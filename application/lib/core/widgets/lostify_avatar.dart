import 'package:flutter/material.dart';

class LostifyAvatar extends StatelessWidget {
  const LostifyAvatar({
    super.key,
    this.imageUrl,
    this.initials = 'WA',
    this.size = 40,
    this.backgroundColor,
    this.foregroundColor,
  });

  final String? imageUrl;
  final String initials;
  final double size;
  final Color? backgroundColor;
  final Color? foregroundColor;

  @override
  Widget build(BuildContext context) {
    final avatarColor = backgroundColor ?? Theme.of(context).colorScheme.primaryContainer;
    final textColor = foregroundColor ?? Theme.of(context).colorScheme.onPrimaryContainer;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: avatarColor,
        shape: BoxShape.circle,
        image: imageUrl != null
            ? DecorationImage(
                image: NetworkImage(imageUrl!),
                fit: BoxFit.cover,
              )
            : null,
      ),
      child: imageUrl == null
          ? Center(
              child: Text(
                initials,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: textColor,
                  fontSize: (size * 0.34).clamp(10, 18),
                ),
              ),
            )
          : null,
    );
  }
}
