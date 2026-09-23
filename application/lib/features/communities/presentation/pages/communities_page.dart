import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../../../core/widgets/lostify_search_bar.dart';
import '../../data/community_repository.dart';

class CommunitiesPage extends StatefulWidget {
  const CommunitiesPage({super.key, this.repository = const MockCommunityRepository()});

  final CommunityRepository repository;

  @override
  State<CommunitiesPage> createState() => _CommunitiesPageState();
}

enum _CommunitiesState { loading, success, empty, error }

class _CommunitiesPageState extends State<CommunitiesPage> {
  final _searchController = TextEditingController();
  _CommunitiesState _state = _CommunitiesState.loading;
  List<Community> _communities = const [];
  String _query = '';
  final Set<String> _joinedIds = {};

  @override
  void initState() {
    super.initState();
    _loadCommunities();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadCommunities() async {
    setState(() => _state = _CommunitiesState.loading);
    try {
      final communities = await widget.repository.getNearbyCommunities();
      if (!mounted) return;
      setState(() {
        _communities = communities;
        _joinedIds
          ..clear()
          ..addAll(communities.where((community) => community.joined).map((community) => community.id));
        _state = communities.isEmpty ? _CommunitiesState.empty : _CommunitiesState.success;
      });
    } catch (_) {
      if (mounted) setState(() => _state = _CommunitiesState.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _communities.where((community) {
      final query = _query.toLowerCase();
      return community.name.toLowerCase().contains(query) || community.tags.any((tag) => tag.toLowerCase().contains(query));
    }).toList();

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: const Text('Communities'),
        actions: [IconButton(onPressed: _loadCommunities, icon: const Icon(Icons.refresh_rounded), tooltip: 'Refresh communities')],
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.xxl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LostifySearchBar(
              hintText: 'Search communities',
              controller: _searchController,
              onChanged: (value) => setState(() => _query = value),
            ),
            const SizedBox(height: AppSpacing.xxl),
            Text('Nearby communities', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.xs),
            Text('Places active around you right now.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
            const SizedBox(height: AppSpacing.lg),
            Expanded(child: _buildContent(filtered)),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(List<Community> filtered) {
    switch (_state) {
      case _CommunitiesState.loading:
        return ListView.separated(
          itemCount: 3,
          separatorBuilder: (_, index) => const SizedBox(height: AppSpacing.md),
          itemBuilder: (context, index) => Container(height: 244, decoration: BoxDecoration(color: AppColors.surfaceVariant, borderRadius: BorderRadius.circular(AppRadius.l))),
        );
      case _CommunitiesState.error:
        return _StateMessage(icon: Icons.cloud_off_rounded, title: 'Communities are unavailable', message: 'We could not load nearby communities.', action: 'Try again', onAction: _loadCommunities);
      case _CommunitiesState.empty:
        return const _StateMessage(icon: Icons.groups_outlined, title: 'No communities nearby', message: 'New communities will appear here as they open.');
      case _CommunitiesState.success:
        if (filtered.isEmpty) {
          return const _StateMessage(icon: Icons.search_off_rounded, title: 'No communities found', message: 'Try a different name or tag.');
        }
        return ListView.separated(
          itemCount: filtered.length,
          separatorBuilder: (_, index) => const SizedBox(height: AppSpacing.md),
          itemBuilder: (context, index) => _CommunityCard(
            community: filtered[index],
            joined: _joinedIds.contains(filtered[index].id),
            onJoin: () => setState(() {
              final id = filtered[index].id;
              _joinedIds.contains(id) ? _joinedIds.remove(id) : _joinedIds.add(id);
            }),
          ),
        );
    }
  }
}

class _CommunityCard extends StatelessWidget {
  const _CommunityCard({required this.community, required this.joined, required this.onJoin});

  final Community community;
  final bool joined;
  final VoidCallback onJoin;

  @override
  Widget build(BuildContext context) {
    return LostifyCard(
      onTap: () => context.push('/community/${community.id}'),
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(AppRadius.l)),
            child: Image.network(
              community.image,
              height: 142,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => const SizedBox(height: 142, child: Center(child: Icon(Icons.image_not_supported_outlined))),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(community.name, style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: AppSpacing.xs),
                      Text(community.distance, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                      const SizedBox(height: AppSpacing.sm),
                      Row(
                        children: [
                          const Icon(Icons.groups_outlined, size: 16, color: AppColors.textSecondary),
                          const SizedBox(width: AppSpacing.xs),
                          Text('${_formatCount(community.members)} members', style: Theme.of(context).textTheme.bodySmall),
                          const SizedBox(width: AppSpacing.md),
                          const Icon(Icons.circle, size: 8, color: AppColors.success),
                          const SizedBox(width: AppSpacing.xs),
                          Text('${_formatCount(community.activeUsers)} active', style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                OutlinedButton(
                  onPressed: onJoin,
                  style: OutlinedButton.styleFrom(foregroundColor: joined ? AppColors.success : AppColors.primary),
                  child: Text(joined ? 'Joined' : 'Join'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatCount(int count) => count >= 1000 ? '${(count / 1000).toStringAsFixed(count >= 10000 ? 0 : 1)}K' : '$count';
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.icon, required this.title, required this.message, this.action, this.onAction});

  final IconData icon;
  final String title;
  final String message;
  final String? action;
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
          if (action != null) ...[
            const SizedBox(height: AppSpacing.lg),
            OutlinedButton(onPressed: onAction, child: Text(action!)),
          ],
        ],
      ),
    );
  }
}
