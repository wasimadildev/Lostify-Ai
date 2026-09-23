import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../../../core/widgets/lostify_status_badge.dart';

class ReportDetailsPage extends StatefulWidget {
  const ReportDetailsPage({super.key});

  @override
  State<ReportDetailsPage> createState() => _ReportDetailsPageState();
}

class _ReportDetailsPageState extends State<ReportDetailsPage> {
  final _pageController = PageController();
  int _imageIndex = 0;
  bool _saved = false;

  final _images = const [
    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80',
    'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80',
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: const Text('Report details'),
        actions: [
          IconButton(
            onPressed: () => setState(() => _saved = !_saved),
            icon: Icon(_saved ? Icons.bookmark_rounded : Icons.bookmark_border_rounded),
            tooltip: _saved ? 'Remove bookmark' : 'Save report',
          ),
          IconButton(
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Report link copied.'))),
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share report',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: AppSpacing.xxl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 280,
              child: PageView.builder(
                controller: _pageController,
                itemCount: _images.length,
                onPageChanged: (value) => setState(() => _imageIndex = value),
                itemBuilder: (context, index) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(AppRadius.xl),
                    child: Image.network(
                      _images[index],
                      fit: BoxFit.cover,
                      width: double.infinity,
                      errorBuilder: (context, error, stackTrace) => const ColoredBox(
                        color: AppColors.surfaceVariant,
                        child: Center(child: Icon(Icons.image_not_supported_outlined, size: 40)),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _images.length,
                (index) => AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: _imageIndex == index ? 24 : 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: AppSpacing.xs),
                  decoration: BoxDecoration(
                    color: _imageIndex == index ? AppColors.primary : AppColors.borderStrong,
                    borderRadius: BorderRadius.circular(AppRadius.s),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.xxl, AppSpacing.lg, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const LostifyStatusBadge(label: 'Found', color: AppColors.success, backgroundColor: Color(0x1A22A06B)),
                      const Spacer(),
                      Text('F-7821', style: Theme.of(context).textTheme.labelMedium?.copyWith(color: AppColors.textSecondary)),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Text('Black Nike Backpack', style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: AppSpacing.sm),
                  Text('Posted 1 day ago by A. Khan', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
                  const SizedBox(height: AppSpacing.lg),
                  LostifyCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    backgroundColor: AppColors.primary.withValues(alpha: 0.08),
                    borderColor: AppColors.primary.withValues(alpha: 0.16),
                    child: Row(
                      children: [
                        const Icon(Icons.auto_awesome_rounded, color: AppColors.primary),
                        const SizedBox(width: AppSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('92% visual match', style: Theme.of(context).textTheme.titleMedium?.copyWith(color: AppColors.primary)),
                              const SizedBox(height: AppSpacing.xs),
                              Text('Similar shape, colour, and strap details.', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xxl),
                  Text('Location', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.sm),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.location_on_outlined, color: AppColors.primary),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text('F-10 Park, Islamabad, Pakistan\nNear the jogging track gate', style: Theme.of(context).textTheme.bodyLarge),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xxl),
                  Text('Description', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'A black Nike backpack with a small blue keychain on the front zip. It was found near the jogging track and is being kept safe by the reporter.',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSecondary, height: 1.5),
                  ),
                  const SizedBox(height: AppSpacing.xxl),
                  LostifyButton(
                    onPressed: () => context.push('/chat'),
                    label: 'Message the finder',
                    icon: Icons.chat_bubble_outline_rounded,
                    width: double.infinity,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
