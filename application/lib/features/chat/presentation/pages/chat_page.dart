import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [
    const _ChatMessage(sender: 'A. Khan', text: 'I think I found this backpack near F-10 Park.', isMe: false),
    const _ChatMessage(sender: 'You', text: 'That sounds like mine. Does it have a blue keychain?', isMe: true),
    const _ChatMessage(sender: 'A. Khan', text: 'Yes, it does. I can meet you by the jogging track gate.', isMe: false),
  ];
  bool _sending = false;

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _messages.add(_ChatMessage(sender: 'You', text: text, isMe: true));
      _messageController.clear();
      _sending = true;
    });
    _scrollToEnd();
    await Future<void>.delayed(const Duration(milliseconds: 850));
    if (!mounted) return;
    setState(() {
      _sending = false;
      _messages.add(const _ChatMessage(sender: 'A. Khan', text: 'Great, I will keep it with me until we meet.', isMe: false));
    });
    _scrollToEnd();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        titleSpacing: 0,
        title: Row(
          children: [
            const CircleAvatar(radius: 18, backgroundColor: AppColors.primary, child: Icon(Icons.person_rounded, color: Colors.white, size: 20)),
            const SizedBox(width: AppSpacing.sm),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('A. Khan', style: Theme.of(context).textTheme.titleMedium),
                Text('Finder · Usually replies quickly', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.success)),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Calling is available after contact verification.'))),
            icon: const Icon(Icons.call_outlined),
            tooltip: 'Call finder',
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, 0),
            child: _ReportContextCard(),
          ),
          Expanded(
            child: _messages.isEmpty
                ? const Center(child: Text('Start the conversation'))
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) => _MessageBubble(message: _messages[index]),
                  ),
          ),
          if (_sending)
            Padding(
              padding: const EdgeInsets.only(left: AppSpacing.lg, bottom: AppSpacing.sm),
              child: Align(alignment: Alignment.centerLeft, child: Text('A. Khan is typing...', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.textSecondary))),
            ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.md),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  IconButton(onPressed: () {}, icon: const Icon(Icons.add_circle_outline_rounded), tooltip: 'Add attachment'),
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.newline,
                      decoration: InputDecoration(
                        hintText: 'Write a message...',
                        filled: true,
                        fillColor: AppColors.surface,
                        contentPadding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.md),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(AppRadius.xl), borderSide: const BorderSide(color: AppColors.border)),
                        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(AppRadius.xl), borderSide: const BorderSide(color: AppColors.border)),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  IconButton(
                    onPressed: _sending ? null : _sendMessage,
                    icon: const Icon(Icons.send_rounded),
                    style: IconButton.styleFrom(backgroundColor: AppColors.primary, foregroundColor: Colors.white),
                    tooltip: 'Send message',
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReportContextCard extends StatelessWidget {
  const _ReportContextCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(AppRadius.m),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(color: AppColors.primary.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(AppRadius.s)),
            child: const Icon(Icons.backpack_outlined, color: AppColors.primary),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Black Nike Backpack', style: Theme.of(context).textTheme.labelLarge),
                Text('92% visual match · F-10 Park', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final _ChatMessage message;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.76),
        margin: const EdgeInsets.only(bottom: AppSpacing.md),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
        decoration: BoxDecoration(
          color: message.isMe ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(AppRadius.l),
            topRight: const Radius.circular(AppRadius.l),
            bottomLeft: Radius.circular(message.isMe ? AppRadius.l : AppRadius.s),
            bottomRight: Radius.circular(message.isMe ? AppRadius.s : AppRadius.l),
          ),
          border: message.isMe ? null : Border.all(color: AppColors.border),
        ),
        child: Text(message.text, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: message.isMe ? Colors.white : AppColors.textPrimary)),
      ),
    );
  }
}

class _ChatMessage {
  const _ChatMessage({required this.sender, required this.text, required this.isMe});

  final String sender;
  final String text;
  final bool isMe;
}
