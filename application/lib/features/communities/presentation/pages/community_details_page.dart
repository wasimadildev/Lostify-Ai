import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../data/community_repository.dart';

class CommunityDetailsPage extends StatefulWidget {
  const CommunityDetailsPage({super.key, required this.communityId, this.repository = const MockCommunityRepository()});

  final String communityId;
  final CommunityRepository repository;

  @override
  State<CommunityDetailsPage> createState() => _CommunityDetailsPageState();
}

enum _CommunityDetailsState { loading, success, error }

class _CommunityDetailsPageState extends State<CommunityDetailsPage> {
  _CommunityDetailsState _state = _CommunityDetailsState.loading;
  Community? _community;
  bool _joined = false;
  String _section = 'Posts';
  final Set<String> _likedPosts = {};

  @override
  void initState() {
    super.initState();
    _loadCommunity();
  }

  Future<void> _loadCommunity() async {
    setState(() => _state = _CommunityDetailsState.loading);
    try {
      final community = await widget.repository.getCommunity(widget.communityId);
      if (!mounted) return;
      setState(() {
        _community = community;
        _joined = community.joined;
        _state = _CommunityDetailsState.success;
      });
    } catch (_) {
      if (mounted) setState(() => _state = _CommunityDetailsState.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final community = _community;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: Text(community?.name ?? 'Community'),
        actions: [IconButton(onPressed: _loadCommunity, icon: const Icon(Icons.refresh_rounded), tooltip: 'Refresh community')],
      ),
      body: switch (_state) {
        _CommunityDetailsState.loading => const _LoadingCommunity(),
        _CommunityDetailsState.error => _ErrorCommunity(onRetry: _loadCommunity),
        _CommunityDetailsState.success => _buildDetails(context, community!),
      },
      floatingActionButton: _state == _CommunityDetailsState.success && _joined
          ? FloatingActionButton.extended(
              onPressed: () => context.push('/community/${widget.communityId}/post/new'),
              icon: const Icon(Icons.edit_rounded),
              label: const Text('New post'),
            )
          : null,
    );
  }

  Widget _buildDetails(BuildContext context, Community community) {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                height: 190,
                width: double.infinity,
                child: Image.network(
                  community.image,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => const ColoredBox(color: AppColors.surfaceVariant, child: Icon(Icons.image_not_supported_outlined)),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: Text(community.name, style: Theme.of(context).textTheme.headlineSmall)),
                        OutlinedButton(
                          onPressed: () => setState(() => _joined = !_joined),
                          child: Text(_joined ? 'Joined' : 'Join'),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(community.description, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary, height: 1.4)),
                    const SizedBox(height: AppSpacing.md),
                    Wrap(spacing: AppSpacing.sm, runSpacing: AppSpacing.sm, children: community.tags.map((tag) => Chip(label: Text('#$tag'))).toList()),
                    const SizedBox(height: AppSpacing.lg),
                    Row(
                      children: [
                        _Stat(icon: Icons.groups_outlined, value: '${_formatCount(community.members)} members'),
                        const SizedBox(width: AppSpacing.sm),
                        _Stat(icon: Icons.circle, value: '${_formatCount(community.activeUsers)} active', active: true),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    LostifyCard(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      backgroundColor: AppColors.primary.withValues(alpha: 0.07),
                      borderColor: AppColors.primary.withValues(alpha: 0.14),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.campaign_outlined, color: AppColors.primary),
                          const SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Admin announcement', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: AppColors.primary)),
                                const SizedBox(height: AppSpacing.xs),
                                Text(community.announcement, style: Theme.of(context).textTheme.bodyMedium),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xxl),
                    SegmentedButton<String>(
                      segments: const [ButtonSegment(value: 'Posts', label: Text('Posts')), ButtonSegment(value: 'Members', label: Text('Members'))],
                      selected: {_section},
                      onSelectionChanged: (selection) => setState(() => _section = selection.first),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (_section == 'Posts')
          if (community.posts.isEmpty)
            const SliverFillRemaining(hasScrollBody: false, child: _EmptySection(icon: Icons.forum_outlined, title: 'No posts yet', message: 'Be the first person to share an update.'))
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, 100),
              sliver: SliverList.separated(
                itemCount: community.posts.length,
                separatorBuilder: (_, index) => const SizedBox(height: AppSpacing.md),
                itemBuilder: (context, index) => _PostCard(
                  post: community.posts[index],
                  liked: _likedPosts.contains(community.posts[index].id) || community.posts[index].liked,
                  onLike: () => setState(() {
                    final id = community.posts[index].id;
                    _likedPosts.contains(id) ? _likedPosts.remove(id) : _likedPosts.add(id);
                  }),
                  onTap: () => context.push('/community/${widget.communityId}/post/${community.posts[index].id}'),
                ),
              ),
            )
        else
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, 100),
            sliver: SliverList.separated(
              itemCount: community.membersList.length,
              separatorBuilder: (_, index) => const SizedBox(height: AppSpacing.sm),
              itemBuilder: (context, index) => _MemberTile(member: community.membersList[index]),
            ),
          ),
      ],
    );
  }

  String _formatCount(int count) => count >= 1000 ? '${(count / 1000).toStringAsFixed(count >= 10000 ? 0 : 1)}K' : '$count';
}

class _PostCard extends StatelessWidget {
  const _PostCard({required this.post, required this.liked, required this.onLike, required this.onTap});

  final CommunityPost post;
  final bool liked;
  final VoidCallback onLike;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return LostifyCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(radius: 19, backgroundColor: AppColors.primary, child: Text(post.authorInitials, style: const TextStyle(color: Colors.white, fontSize: 12))),
              const SizedBox(width: AppSpacing.sm),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(post.author, style: Theme.of(context).textTheme.labelLarge), Text(post.time, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary))])),
              const Icon(Icons.more_horiz_rounded, color: AppColors.textSecondary),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Text(post.title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.xs),
          Text(post.body, maxLines: 3, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary, height: 1.4)),
          if (post.image != null) ...[
            const SizedBox(height: AppSpacing.md),
            ClipRRect(borderRadius: BorderRadius.circular(AppRadius.m), child: Image.network(post.image!, height: 150, width: double.infinity, fit: BoxFit.cover)),
          ],
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              IconButton(onPressed: onLike, icon: Icon(liked ? Icons.favorite_rounded : Icons.favorite_border_rounded, color: liked ? AppColors.error : AppColors.textSecondary), tooltip: 'Like post'),
              Text('${post.likes + (liked && !post.liked ? 1 : 0)}'),
              const SizedBox(width: AppSpacing.lg),
              const Icon(Icons.comment_outlined, size: 19, color: AppColors.textSecondary),
              const SizedBox(width: AppSpacing.xs),
              Text('${post.commentCount}'),
              const Spacer(),
              IconButton(onPressed: () => onTap(), icon: const Icon(Icons.share_outlined, color: AppColors.textSecondary), tooltip: 'Share post'),
            ],
          ),
        ],
      ),
    );
  }
}

class _MemberTile extends StatelessWidget {
  const _MemberTile({required this.member});

  final CommunityMember member;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      tileColor: AppColors.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.m), side: const BorderSide(color: AppColors.border)),
      leading: CircleAvatar(backgroundColor: AppColors.primary.withValues(alpha: 0.12), child: Text(member.initials, style: const TextStyle(color: AppColors.primary))),
      title: Text(member.name),
      subtitle: Text(member.role),
      trailing: member.active ? const Icon(Icons.circle, size: 10, color: AppColors.success) : null,
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.icon, required this.value, this.active = false});

  final IconData icon;
  final String value;
  final bool active;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: AppSpacing.sm),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(AppRadius.m)),
      child: Row(children: [Icon(icon, size: 16, color: active ? AppColors.success : AppColors.textSecondary), const SizedBox(width: AppSpacing.xs), Text(value, style: Theme.of(context).textTheme.bodySmall)]),
    );
  }
}

class _LoadingCommunity extends StatelessWidget {
  const _LoadingCommunity();

  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

class _ErrorCommunity extends StatelessWidget {
  const _ErrorCommunity({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.cloud_off_rounded, size: 48, color: AppColors.textTertiary), const SizedBox(height: AppSpacing.lg), const Text('Could not load this community'), const SizedBox(height: AppSpacing.lg), OutlinedButton(onPressed: onRetry, child: const Text('Try again'))]));
}

class _EmptySection extends StatelessWidget {
  const _EmptySection({required this.icon, required this.title, required this.message});

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) => Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(icon, size: 44, color: AppColors.textTertiary), const SizedBox(height: AppSpacing.md), Text(title, style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: AppSpacing.xs), Text(message, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary))]));
}
