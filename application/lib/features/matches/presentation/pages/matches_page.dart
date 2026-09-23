import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../../../core/widgets/lostify_status_badge.dart';

class MatchesPage extends StatefulWidget {
  const MatchesPage({super.key});

  @override
  State<MatchesPage> createState() => _MatchesPageState();
}

enum _MatchesState { loading, success, empty, error }

class _MatchesPageState extends State<MatchesPage> {
  _MatchesState _state = _MatchesState.loading;
  String _sort = 'Best match';
  Timer? _loadTimer;

  final List<_Match> _matches = const [
    _Match(
      title: 'Black Nike Backpack',
      status: 'Found',
      score: 0.92,
      location: 'F-10 Park',
      posted: 'Posted 1 day ago',
      id: 'F-7821',
      image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80',
    ),
    _Match(
      title: 'University Backpack',
      status: 'Lost',
      score: 0.84,
      location: 'Shifa University',
      posted: 'Posted 3 days ago',
      id: 'L-4451',
      image: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _loadMatches();
  }

  void _loadMatches() {
    _loadTimer?.cancel();
    setState(() => _state = _MatchesState.loading);
    _loadTimer = Timer(const Duration(milliseconds: 650), () {
      if (mounted) setState(() => _state = _matches.isEmpty ? _MatchesState.empty : _MatchesState.success);
    });
  }

  @override
  void dispose() {
    _loadTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: const Text('Possible matches'),
        actions: [
          IconButton(onPressed: _loadMatches, icon: const Icon(Icons.refresh_rounded), tooltip: 'Refresh matches'),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.xxl),
        child: _buildState(context),
      ),
    );
  }

  Widget _buildState(BuildContext context) {
    switch (_state) {
      case _MatchesState.loading:
        return const _LoadingMatches();
      case _MatchesState.error:
        return _StateMessage(
          icon: Icons.wifi_off_rounded,
          title: 'Could not load matches',
          message: 'Check your connection and try again.',
          actionLabel: 'Try again',
          onAction: _loadMatches,
        );
      case _MatchesState.empty:
        return const _StateMessage(
          icon: Icons.search_off_rounded,
          title: 'No close matches yet',
          message: 'We will keep looking as new reports arrive.',
        );
      case _MatchesState.success:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('We found ${_matches.length} reports worth reviewing.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
            const SizedBox(height: AppSpacing.lg),
            Align(
              alignment: Alignment.centerRight,
              child: PopupMenuButton<String>(
                initialValue: _sort,
                onSelected: (value) => setState(() => _sort = value),
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'Best match', child: Text('Best match')),
                  PopupMenuItem(value: 'Newest first', child: Text('Newest first')),
                ],
                child: OutlinedButton.icon(
                  onPressed: null,
                  icon: const Icon(Icons.tune_rounded),
                  label: Text(_sort),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Expanded(
              child: ListView.separated(
                itemCount: _matches.length,
                separatorBuilder: (_, index) => const SizedBox(height: AppSpacing.md),
                itemBuilder: (context, index) => _MatchCard(match: _matches[index]),
              ),
            ),
          ],
        );
    }
  }
}

class _MatchCard extends StatelessWidget {
  const _MatchCard({required this.match});

  final _Match match;

  @override
  Widget build(BuildContext context) {
    final percentage = (match.score * 100).round();
    return LostifyCard(
      onTap: () => context.push('/report/details'),
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(AppRadius.l)),
                child: Image.network(
                  match.image,
                  height: 172,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => const SizedBox(height: 172, child: Center(child: Icon(Icons.image_not_supported_outlined))),
                ),
              ),
              Positioned(
                top: AppSpacing.md,
                right: AppSpacing.md,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: AppSpacing.xs),
                  decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(AppRadius.s)),
                  child: Text('$percentage% match', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: AppColors.primary)),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(match.title, style: Theme.of(context).textTheme.titleMedium)),
                    LostifyStatusBadge(
                      label: match.status,
                      color: match.status == 'Found' ? AppColors.success : AppColors.error,
                      backgroundColor: (match.status == 'Found' ? AppColors.success : AppColors.error).withValues(alpha: 0.12),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(match.posted, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                const SizedBox(height: AppSpacing.md),
                LinearProgressIndicator(
                  value: match.score,
                  minHeight: 8,
                  borderRadius: BorderRadius.circular(AppRadius.s),
                  backgroundColor: AppColors.border,
                  valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
                ),
                const SizedBox(height: AppSpacing.md),
                Row(
                  children: [
                    const Icon(Icons.location_on_outlined, size: 18, color: AppColors.textSecondary),
                    const SizedBox(width: AppSpacing.xs),
                    Expanded(child: Text(match.location, style: Theme.of(context).textTheme.bodyMedium)),
                    Text(match.id, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingMatches extends StatelessWidget {
  const _LoadingMatches();

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        const SizedBox(height: AppSpacing.md),
        const LinearProgressIndicator(),
        const SizedBox(height: AppSpacing.xl),
        Text('Finding the closest reports...', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: AppSpacing.sm),
        Text('Comparing visual details and location signals.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
        const SizedBox(height: AppSpacing.xxl),
        ...List.generate(
          2,
          (index) => Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.md),
            child: Container(
              height: 270,
              decoration: BoxDecoration(color: AppColors.surfaceVariant, borderRadius: BorderRadius.circular(AppRadius.l)),
            ),
          ),
        ),
      ],
    );
  }
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.icon, required this.title, required this.message, this.actionLabel, this.onAction});

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 48, color: AppColors.textTertiary),
          const SizedBox(height: AppSpacing.lg),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.xs),
          Text(message, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
          if (actionLabel != null) ...[
            const SizedBox(height: AppSpacing.lg),
            OutlinedButton(onPressed: onAction, child: Text(actionLabel!)),
          ],
        ],
      ),
    );
  }
}

class _Match {
  const _Match({required this.title, required this.status, required this.score, required this.location, required this.posted, required this.id, required this.image});

  final String title;
  final String status;
  final double score;
  final String location;
  final String posted;
  final String id;
  final String image;
}
