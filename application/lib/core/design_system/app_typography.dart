import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTypography {
  const AppTypography._();

  static TextTheme get textTheme => GoogleFonts.interTextTheme(
        const TextTheme(
          displayLarge: TextStyle(fontSize: 40, height: 1.1, fontWeight: FontWeight.w700),
          displayMedium: TextStyle(fontSize: 32, height: 1.2, fontWeight: FontWeight.w700),
          headlineLarge: TextStyle(fontSize: 28, height: 1.2, fontWeight: FontWeight.w700),
          headlineMedium: TextStyle(fontSize: 24, height: 1.3, fontWeight: FontWeight.w600),
          titleLarge: TextStyle(fontSize: 22, height: 1.3, fontWeight: FontWeight.w600),
          titleMedium: TextStyle(fontSize: 18, height: 1.3, fontWeight: FontWeight.w600),
          bodyLarge: TextStyle(fontSize: 16, height: 1.5, fontWeight: FontWeight.w400),
          bodyMedium: TextStyle(fontSize: 14, height: 1.5, fontWeight: FontWeight.w400),
          bodySmall: TextStyle(fontSize: 12, height: 1.45, fontWeight: FontWeight.w400),
          labelLarge: TextStyle(fontSize: 14, height: 1.4, fontWeight: FontWeight.w600),
          labelMedium: TextStyle(fontSize: 12, height: 1.4, fontWeight: FontWeight.w500),
          labelSmall: TextStyle(fontSize: 11, height: 1.4, fontWeight: FontWeight.w500),
        ),
      );

  static const TextStyle displayLarge = TextStyle(
    fontSize: 40,
    height: 1.1,
    fontWeight: FontWeight.w700,
  );

  static const TextStyle displayMedium = TextStyle(
    fontSize: 32,
    height: 1.2,
    fontWeight: FontWeight.w700,
  );

  static const TextStyle headlineLarge = TextStyle(
    fontSize: 28,
    height: 1.2,
    fontWeight: FontWeight.w700,
  );

  static const TextStyle headlineMedium = TextStyle(
    fontSize: 24,
    height: 1.3,
    fontWeight: FontWeight.w600,
  );

  static const TextStyle titleLarge = TextStyle(
    fontSize: 22,
    height: 1.3,
    fontWeight: FontWeight.w600,
  );

  static const TextStyle titleMedium = TextStyle(
    fontSize: 18,
    height: 1.3,
    fontWeight: FontWeight.w600,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    height: 1.5,
    fontWeight: FontWeight.w400,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    height: 1.5,
    fontWeight: FontWeight.w400,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 12,
    height: 1.45,
    fontWeight: FontWeight.w400,
  );

  static const TextStyle labelLarge = TextStyle(
    fontSize: 14,
    height: 1.4,
    fontWeight: FontWeight.w600,
  );

  static const TextStyle labelMedium = TextStyle(
    fontSize: 12,
    height: 1.4,
    fontWeight: FontWeight.w500,
  );

  static const TextStyle caption = TextStyle(
    fontSize: 11,
    height: 1.4,
    fontWeight: FontWeight.w500,
  );
}
