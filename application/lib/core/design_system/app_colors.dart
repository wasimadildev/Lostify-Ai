import 'package:flutter/material.dart';

class AppColors {
  const AppColors._();

  static const Color primary = Color(0xFF4F36D9);
  static const Color primaryDark = Color(0xFF3824A8);
  static const Color primaryLight = Color(0xFF6D55E8);
  static const Color accent = Color(0xFF7C5CFF);

  static const Color background = Color(0xFFF8F8FC);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceVariant = Color(0xFFF4F3FB);
  static const Color textPrimary = Color(0xFF111118);
  static const Color textSecondary = Color(0xFF6B6B78);
  static const Color textTertiary = Color(0xFF8D8D9A);
  static const Color border = Color(0xFFE6E6EF);
  static const Color borderStrong = Color(0xFFCFCFE1);

  static const Color success = Color(0xFF22A06B);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFDC3B4A);
  static const Color info = Color(0xFF3B82F6);

  static const Color onPrimary = Colors.white;
  static const Color darkBackground = Color(0xFF0F1220);
  static const Color darkSurface = Color(0xFF171B2B);
  static const Color darkTextPrimary = Color(0xFFF7F7FB);
  static const Color darkTextSecondary = Color(0xFFB5B6C5);
  static const Color darkBorder = Color(0xFF2C3043);

  static const LinearGradient brandGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [primary, primaryLight],
  );

  static const LinearGradient softGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFFFCFCFF), Color(0xFFF4F3FB)],
  );
}
