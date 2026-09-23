import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../../../core/widgets/lostify_search_bar.dart';
import '../../../../core/widgets/lostify_status_badge.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _filter = 'All';

  final List<_HomeReport> _reports = const [
    _HomeReport(
      title: 'Black Nike Backpack',
      status: 'Lost',
      category: 'Items',
      time: '3 days ago',
      location: 'Islamabad, Pakistan',
      image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80',
    ),
    _HomeReport(
      title: 'Golden Retriever',
      status: 'Found',
      category: 'Pets',
      time: '1 day ago',
      location: 'F-10 Park',
      image: 'https://images.unsplash.com/photo-1552053831-71594a27632d?auto=format&fit=crop&w=900&q=80',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final visibleReports = _filter == 'All'
        ? _reports
        : _reports.where((report) => report.category == _filter).toList();

    return Builder(
      builder: (context) => SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            sliver: SliverToBoxAdapter(child: _Header(onMenuTap: () => Scaffold.of(context).openDrawer())),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            sliver: const SliverToBoxAdapter(
              child: LostifySearchBar(hintText: 'Search lost or found reports'),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            sliver: SliverToBoxAdapter(child: _CreateReportCard(onTap: () => context.push('/report'))),
          ),
          SliverToBoxAdapter(
            child: SizedBox(
              height: 60,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, AppSpacing.sm),
                scrollDirection: Axis.horizontal,
                children: ['All', 'Items', 'Pets', 'People'].map((filter) {
                  final selected = _filter == filter;
                  return Padding(
                    padding: const EdgeInsets.only(right: AppSpacing.sm),
                    child: ChoiceChip(
                      label: Text(filter),
                      selected: selected,
                      onSelected: (_) => setState(() => _filter = filter),
                      selectedColor: AppColors.primary,
                      labelStyle: TextStyle(color: selected ? Colors.white : AppColors.textPrimary),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.xxl),
            sliver: visibleReports.isEmpty
                ? const SliverFillRemaining(hasScrollBody: false, child: _EmptyReports())
                : SliverList.builder(
                    itemCount: visibleReports.length,
                    itemBuilder: (context, index) => Padding(
                      padding: const EdgeInsets.only(bottom: AppSpacing.md),
                      child: _ReportCard(report: visibleReports[index]),
                    ),
                  ),
          ),
        ],
      ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.onMenuTap});

  final VoidCallback onMenuTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          onPressed: onMenuTap,
          icon: const Icon(Icons.menu_rounded),
          style: IconButton.styleFrom(
            backgroundColor: AppColors.surface,
            side: const BorderSide(color: AppColors.border),
          ),
          tooltip: 'Open menu',
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Good morning, Waseem', style: Theme.of(context).textTheme.titleLarge),
              Text(
                'Let’s help something find its way home.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
        IconButton(
          onPressed: () => context.go('/alerts'),
          icon: const Icon(Icons.notifications_none_rounded),
          style: IconButton.styleFrom(
            backgroundColor: AppColors.surface,
            side: const BorderSide(color: AppColors.border),
          ),
          tooltip: 'View alerts',
        ),
      ],
    );
  }
}

class _CreateReportCard extends StatelessWidget {
  const _CreateReportCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return LostifyCard(
      onTap: onTap,
      padding: const EdgeInsets.all(AppSpacing.lg),
      backgroundColor: AppColors.primary,
      borderColor: Colors.transparent,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Report lost or found', style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white)),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  'Give AI the details it needs to help.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white.withValues(alpha: 0.8)),
                ),
              ],
            ),
          ),
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(AppRadius.m),
            ),
            child: const Icon(Icons.add_rounded, color: Colors.white),
          ),
        ],
      ),
    );
  }
}

class _ReportCard extends StatelessWidget {
  const _ReportCard({required this.report});

  final _HomeReport report;

  @override
  Widget build(BuildContext context) {
    final statusColor = report.status == 'Found' ? AppColors.success : AppColors.error;
    return LostifyCard(
      onTap: () => context.push('/report/details'),
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(AppRadius.l)),
            child: Image.network(
              report.image,
              height: 156,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => const SizedBox(
                height: 156,
                child: Center(child: Icon(Icons.image_not_supported_outlined)),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(report.title, style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: AppSpacing.sm),
                      Row(
                        children: [
                          LostifyStatusBadge(
                            label: report.status,
                            color: statusColor,
                            backgroundColor: statusColor.withValues(alpha: 0.12),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Text(report.time, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text(report.location, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyReports extends StatelessWidget {
  const _EmptyReports();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.inbox_outlined, size: 48, color: AppColors.textTertiary),
          const SizedBox(height: AppSpacing.md),
          Text('No reports in this category', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.xs),
          Text('Try another filter.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}

class _HomeReport {
  const _HomeReport({required this.title, required this.status, required this.category, required this.time, required this.location, required this.image});

  final String title;
  final String status;
  final String category;
  final String time;
  final String location;
  final String image;
}
