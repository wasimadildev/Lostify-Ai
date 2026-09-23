import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_card.dart';
import '../../data/community_repository.dart';

class CommunityPostPage extends StatefulWidget {
  const CommunityPostPage({super.key, required this.communityId, required this.postId, this.repository = const MockCommunityRepository()});

  final String communityId;
  final String postId;
  final CommunityRepository repository;

  @override
  State<CommunityPostPage> createState() => _CommunityPostPageState();
}

enum _PostState { loading, success, empty, error }

class _CommunityPostPageState extends State<CommunityPostPage> {
  final _commentController = TextEditingController();
  final _titleController = TextEditingController();
  final _bodyController = TextEditingController();
  _PostState _state = _PostState.loading;
  List<CommunityComment> _comments = const [];
  CommunityPost? _post;
  bool _liked = false;
  bool _sendingComment = false;
  bool _publishing = false;

  bool get _isComposer => widget.postId == 'new';

  @override
  void initState() {
    super.initState();
    if (_isComposer) {
      _state = _PostState.success;
    } else {
      _loadPost();
    }
  }

  @override
  void dispose() {
    _commentController.dispose();
    _titleController.dispose();
    _bodyController.dispose();
    super.dispose();
  }

  Future<void> _loadPost() async {
    setState(() => _state = _PostState.loading);
    try {
      final post = await widget.repository.getPost(widget.communityId, widget.postId);
      final comments = await widget.repository.getComments(widget.communityId, widget.postId);
      if (!mounted) return;
      setState(() {
        _post = post;
        _liked = post.liked;
        _comments = comments;
        _state = _PostState.success;
      });
    } catch (_) {
      if (mounted) setState(() => _state = _PostState.error);
    }
  }

  Future<void> _addComment() async {
    final text = _commentController.text.trim();
    if (text.isEmpty || _sendingComment) return;
    setState(() {
      _sendingComment = true;
      _commentController.clear();
      _comments = [
        ..._comments,
        CommunityComment(author: 'You', initials: 'WA', text: text, time: 'Just now', likes: 0, liked: false),
      ];
    });
    await Future<void>.delayed(const Duration(milliseconds: 450));
    if (mounted) setState(() => _sendingComment = false);
  }

  Future<void> _publishPost() async {
    if (_titleController.text.trim().length < 3 || _bodyController.text.trim().length < 10) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Add a title and a few details first.')));
      return;
    }
    setState(() => _publishing = true);
    await Future<void>.delayed(const Duration(milliseconds: 650));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Your post was published.')));
    context.pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: Text(_isComposer ? 'New post' : 'Post details'),
        actions: [
          if (!_isComposer) IconButton(onPressed: _loadPost, icon: const Icon(Icons.refresh_rounded), tooltip: 'Refresh post'),
        ],
      ),
      body: _isComposer ? _buildComposer(context) : _buildPostState(context),
    );
  }

  Widget _buildComposer(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, AppSpacing.xxl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Share an update', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.xs),
          Text('Keep your community informed with a clear, useful post.', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: AppSpacing.xxl),
          TextField(controller: _titleController, decoration: const InputDecoration(labelText: 'Title', hintText: 'Found a wallet near the market')), 
          const SizedBox(height: AppSpacing.lg),
          TextField(controller: _bodyController, minLines: 6, maxLines: 10, decoration: const InputDecoration(labelText: 'Details', hintText: 'Share what you saw and where others can verify it.')),
          const SizedBox(height: AppSpacing.lg),
          LostifyCard(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Row(children: [const Icon(Icons.photo_outlined, color: AppColors.primary), const SizedBox(width: AppSpacing.sm), const Expanded(child: Text('Add a photo later from the post menu')), IconButton(onPressed: () {}, icon: const Icon(Icons.add_rounded), tooltip: 'Add photo')]),
          ),
          const SizedBox(height: AppSpacing.xxxl),
          LostifyButton(onPressed: _publishPost, label: 'Publish post', loading: _publishing, width: double.infinity),
        ],
      ),
    );
  }

  Widget _buildPostState(BuildContext context) {
    switch (_state) {
      case _PostState.loading:
        return const Center(child: CircularProgressIndicator());
      case _PostState.error:
        return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [const Icon(Icons.cloud_off_rounded, size: 48, color: AppColors.textTertiary), const SizedBox(height: AppSpacing.lg), const Text('Could not load this post'), const SizedBox(height: AppSpacing.lg), OutlinedButton(onPressed: _loadPost, child: const Text('Try again'))]));
      case _PostState.empty:
        return const Center(child: Text('This post is no longer available.'));
      case _PostState.success:
        return _buildPost(context, _post!);
    }
  }

  Widget _buildPost(BuildContext context, CommunityPost post) {
    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.md, AppSpacing.lg, AppSpacing.lg),
            children: [
              Row(children: [CircleAvatar(radius: 21, backgroundColor: AppColors.primary, child: Text(post.authorInitials, style: const TextStyle(color: Colors.white))), const SizedBox(width: AppSpacing.sm), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(post.author, style: Theme.of(context).textTheme.titleSmall), Text(post.time, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary))])), const Icon(Icons.more_horiz_rounded, color: AppColors.textSecondary)]),
              const SizedBox(height: AppSpacing.xl),
              Text(post.title, style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: AppSpacing.sm),
              Text(post.body, style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.5)),
              if (post.image != null) ...[
                const SizedBox(height: AppSpacing.lg),
                ClipRRect(borderRadius: BorderRadius.circular(AppRadius.l), child: Image.network(post.image!, height: 220, width: double.infinity, fit: BoxFit.cover)),
              ],
              const SizedBox(height: AppSpacing.lg),
              Row(
                children: [
                  Expanded(child: OutlinedButton.icon(onPressed: () => setState(() => _liked = !_liked), icon: Icon(_liked ? Icons.favorite_rounded : Icons.favorite_border_rounded, color: _liked ? AppColors.error : null), label: Text(_liked ? '${post.likes + 1} likes' : '${post.likes} likes'))),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(child: OutlinedButton.icon(onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Post link copied.'))), icon: const Icon(Icons.share_outlined), label: const Text('Share'))),
                ],
              ),
              const SizedBox(height: AppSpacing.xxl),
              Row(children: [Text('Comments', style: Theme.of(context).textTheme.titleLarge), const SizedBox(width: AppSpacing.sm), Text('${_comments.length}', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary))]),
              const SizedBox(height: AppSpacing.md),
              if (_comments.isEmpty) const Padding(padding: EdgeInsets.all(AppSpacing.xxl), child: Center(child: Text('Be the first to comment.'))),
              ..._comments.map((comment) => _CommentTile(comment: comment)),
            ],
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.md),
            child: Row(children: [Expanded(child: TextField(controller: _commentController, minLines: 1, maxLines: 3, decoration: InputDecoration(hintText: 'Add a comment...', filled: true, fillColor: AppColors.surface, border: OutlineInputBorder(borderRadius: BorderRadius.circular(AppRadius.xl), borderSide: const BorderSide(color: AppColors.border))))), const SizedBox(width: AppSpacing.sm), IconButton(onPressed: _sendingComment ? null : _addComment, icon: const Icon(Icons.send_rounded), style: IconButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white), tooltip: 'Add comment')]),
          ),
        ),
      ],
    );
  }
}

class _CommentTile extends StatefulWidget {
  const _CommentTile({required this.comment});

  final CommunityComment comment;

  @override
  State<_CommentTile> createState() => _CommentTileState();
}

class _CommentTileState extends State<_CommentTile> {
  late bool _liked = widget.comment.liked;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(radius: 17, backgroundColor: AppColors.primary.withValues(alpha: 0.12), child: Text(widget.comment.initials, style: const TextStyle(color: AppColors.primary, fontSize: 11))),
          const SizedBox(width: AppSpacing.sm),
          Expanded(child: Container(padding: const EdgeInsets.all(AppSpacing.md), decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(AppRadius.m), border: Border.all(color: AppColors.border)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Row(children: [Text(widget.comment.author, style: Theme.of(context).textTheme.labelLarge), const Spacer(), Text(widget.comment.time, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary))]), const SizedBox(height: AppSpacing.xs), Text(widget.comment.text), const SizedBox(height: AppSpacing.xs), InkWell(onTap: () => setState(() => _liked = !_liked), child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(_liked ? Icons.favorite_rounded : Icons.favorite_border_rounded, size: 16, color: _liked ? AppColors.error : AppColors.textSecondary), const SizedBox(width: AppSpacing.xs), Text('${widget.comment.likes + (_liked && !widget.comment.liked ? 1 : 0)}')]))]))),
        ],
      ),
    );
  }
}
