import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/storage/onboarding_repository.dart';
import '../../../../core/widgets/lostify_button.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final PageController _pageController = PageController();
  final OnboardingRepository _onboardingRepository = SharedPreferencesOnboardingRepository();
  int _currentPage = 0;
  bool _saving = false;

  final List<_OnboardingData> _pages = const [
    _OnboardingData(
      title: 'Find what matters',
      description: 'Report lost items, pets, or missing people in seconds.',
      icon: Icons.search_rounded,
      color: AppColors.primary,
    ),
    _OnboardingData(
      title: 'Let AI connect the dots',
      description: 'Visual matching helps surface reports that look like yours.',
      icon: Icons.auto_awesome_rounded,
      color: AppColors.accent,
    ),
    _OnboardingData(
      title: 'Recover with your community',
      description: 'Share the right signal with people nearby who can help.',
      icon: Icons.people_alt_rounded,
      color: AppColors.success,
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _completeOnboarding() async {
    if (_saving) return;
    setState(() => _saving = true);
    await _onboardingRepository.markOnboardingCompleted();
    if (!mounted) return;
    context.go('/login');
  }

  void _nextPage() {
    if (_currentPage < _pages.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 420),
        curve: Curves.easeOutCubic,
      );
    } else {
      _completeOnboarding();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.sm,
            AppSpacing.lg,
            AppSpacing.lg,
          ),
          child: Column(
            children: [
              Row(
                children: [
                  Text('Lostify AI', style: Theme.of(context).textTheme.titleLarge),
                  const Spacer(),
                  TextButton(
                    onPressed: _saving ? null : _completeOnboarding,
                    child: const Text('Skip'),
                  ),
                ],
              ),
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: _pages.length,
                  onPageChanged: (value) => setState(() => _currentPage = value),
                  itemBuilder: (context, index) => _OnboardingSlide(page: _pages[index]),
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  _pages.length,
                  (index) => AnimatedContainer(
                    duration: const Duration(milliseconds: 250),
                    width: _currentPage == index ? 28 : 8,
                    height: 8,
                    margin: const EdgeInsets.symmetric(horizontal: AppSpacing.xs),
                    decoration: BoxDecoration(
                      color: _currentPage == index ? AppColors.primary : AppColors.borderStrong,
                      borderRadius: BorderRadius.circular(AppRadius.s),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.xxl),
              LostifyButton(
                onPressed: _nextPage,
                label: _currentPage == _pages.length - 1 ? 'Get started' : 'Next',
                loading: _saving,
                width: double.infinity,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OnboardingSlide extends StatelessWidget {
  const _OnboardingSlide({required this.page});

  final _OnboardingData page;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 224,
            height: 224,
            decoration: BoxDecoration(
              color: page.color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(AppRadius.xxxl),
              border: Border.all(color: page.color.withValues(alpha: 0.16)),
            ),
            child: Icon(page.icon, size: 88, color: page.color),
          ),
          const SizedBox(height: AppSpacing.xxxl),
          Text(
            page.title,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            page.description,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _OnboardingData {
  const _OnboardingData({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
  });

  final String title;
  final String description;
  final IconData icon;
  final Color color;
}
