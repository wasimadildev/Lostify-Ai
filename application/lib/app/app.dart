import 'package:flutter/material.dart';

import '../core/design_system/app_theme.dart';
import 'router/app_router.dart';

class LostifyApp extends StatelessWidget {
  const LostifyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Lostify AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      routerConfig: appRouter,
    );
  }
}
