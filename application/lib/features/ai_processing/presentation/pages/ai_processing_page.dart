import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';

class AiProcessingPage extends StatefulWidget {
  const AiProcessingPage({super.key});

  @override
  State<AiProcessingPage> createState() => _AiProcessingPageState();
}

class _AiProcessingPageState extends State<AiProcessingPage> with SingleTickerProviderStateMixin {
  late final AnimationController _animationController;
  Timer? _processingTimer;
  int _activeStep = 0;
  bool _failed = false;

  final _steps = const [
    'Reading your photos',
    'Extracting visual features',
    'Searching nearby reports',
    'Ranking the best matches',
  ];

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();
    _startProcessing();
  }

  void _startProcessing() {
    _processingTimer?.cancel();
    setState(() {
      _activeStep = 0;
      _failed = false;
    });
    _processingTimer = Timer.periodic(const Duration(milliseconds: 900), (timer) {
      if (!mounted) return;
      if (_activeStep >= _steps.length - 1) {
        timer.cancel();
        setState(() => _activeStep = _steps.length);
        Future<void>.delayed(const Duration(milliseconds: 550), () {
          if (mounted) context.push('/report/matches');
        });
      } else {
        setState(() => _activeStep++);
      }
    });
  }

  @override
  void dispose() {
    _processingTimer?.cancel();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final complete = _activeStep == _steps.length;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.close_rounded)),
        title: const Text('AI analysis'),
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.xl, AppSpacing.lg, AppSpacing.xxl),
        child: Column(
          children: [
            Text(
              _failed ? 'Something went wrong' : complete ? 'Matches are ready' : 'AI is analysing your report',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              _failed
                  ? 'We could not complete the analysis. Your report is still safe.'
                  : complete
                      ? 'We found a few reports worth reviewing.'
                      : 'We compare visual signals with reports near your selected location.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.xxxl),
            _AnalysisPreview(animation: _animationController, failed: _failed),
            const SizedBox(height: AppSpacing.xxxl),
            if (!_failed)
              Column(
                children: List.generate(
                  _steps.length,
                  (index) => _ProcessingStep(
                    label: _steps[index],
                    completed: index < _activeStep,
                    active: index == _activeStep && !complete,
                  ),
                ),
              ),
            const Spacer(),
            if (_failed)
              LostifyButton(onPressed: _startProcessing, label: 'Try again', width: double.infinity)
            else if (complete)
              LostifyButton(onPressed: () => context.push('/report/matches'), label: 'View matches', width: double.infinity)
            else
              Text(
                'This usually takes a few seconds',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
              ),
          ],
        ),
      ),
    );
  }
}

class _AnalysisPreview extends StatelessWidget {
  const _AnalysisPreview({required this.animation, required this.failed});

  final Animation<double> animation;
  final bool failed;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) => Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 232,
            height: 232,
            child: CircularProgressIndicator(
              value: failed ? 1 : null,
              strokeWidth: 3,
              color: failed ? AppColors.error : AppColors.primary,
              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
            ),
          ),
          Container(
            width: 176,
            height: 176,
            decoration: BoxDecoration(
              color: failed ? AppColors.error.withValues(alpha: 0.08) : AppColors.surfaceVariant,
              borderRadius: BorderRadius.circular(AppRadius.xl),
              border: Border.all(color: failed ? AppColors.error.withValues(alpha: 0.2) : AppColors.border),
            ),
            child: Icon(
              failed ? Icons.cloud_off_rounded : Icons.auto_awesome_rounded,
              size: 64,
              color: failed ? AppColors.error : AppColors.primary,
            ),
          ),
          if (!failed)
            Transform.rotate(
              angle: animation.value * 6.28,
              child: const Align(
                alignment: Alignment.topCenter,
                child: Icon(Icons.circle, size: 10, color: AppColors.accent),
              ),
            ),
        ],
      ),
    );
  }
}

class _ProcessingStep extends StatelessWidget {
  const _ProcessingStep({required this.label, required this.completed, required this.active});

  final String label;
  final bool completed;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final color = completed ? AppColors.success : active ? AppColors.primary : AppColors.borderStrong;
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            child: Icon(completed ? Icons.check_rounded : active ? Icons.more_horiz_rounded : Icons.circle, color: Colors.white, size: 15),
          ),
          const SizedBox(width: AppSpacing.md),
          Text(label, style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: active ? AppColors.primary : AppColors.textPrimary)),
        ],
      ),
    );
  }
}
