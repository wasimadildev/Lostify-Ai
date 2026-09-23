import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/storage/onboarding_repository.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> with SingleTickerProviderStateMixin {
  late final AnimationController _animationController;
  late final Animation<double> _fadeAnimation;
  late final Animation<double> _scaleAnimation;
  final OnboardingRepository _onboardingRepository = SharedPreferencesOnboardingRepository();
  Timer? _navigationTimer;
  String _status = 'Preparing your recovery toolkit';

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..forward();
    _fadeAnimation = CurvedAnimation(parent: _animationController, curve: Curves.easeOutCubic);
    _scaleAnimation = CurvedAnimation(parent: _animationController, curve: Curves.easeOutBack);
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    final completed = await _onboardingRepository.hasCompletedOnboarding();
    if (!mounted) return;
    setState(() => _status = 'Ready when you are');
    _navigationTimer = Timer(const Duration(milliseconds: 900), () {
      if (!mounted) return;
      context.go(completed ? '/login' : '/onboarding');
    });
  }

  @override
  void dispose() {
    _navigationTimer?.cancel();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(gradient: AppColors.brandGradient),
        child: SafeArea(
          child: Center(
            child: AnimatedBuilder(
              animation: _animationController,
              builder: (context, child) => Opacity(
                opacity: _fadeAnimation.value,
                child: Transform.scale(
                  scale: 0.9 + (_scaleAnimation.value * 0.1),
                  child: child,
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 112,
                    height: 112,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(AppRadius.xxxl),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.28)),
                    ),
                    child: const Icon(Icons.location_on_rounded, size: 56, color: Colors.white),
                  ),
                  const SizedBox(height: AppSpacing.xxl),
                  Text(
                    'Lostify AI',
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'AI-Powered Search.\nFaster Recovery.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.white.withValues(alpha: 0.82),
                      height: 1.45,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.huge),
                  SizedBox(
                    width: 132,
                    child: Column(
                      children: [
                        const LinearProgressIndicator(
                          minHeight: 3,
                          backgroundColor: Color(0x55FFFFFF),
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        Text(
                          _status,
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: Colors.white.withValues(alpha: 0.72),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
