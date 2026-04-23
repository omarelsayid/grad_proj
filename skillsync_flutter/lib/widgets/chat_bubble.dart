// lib/widgets/chat_bubble.dart
import 'package:flutter/material.dart';
import '../models/chat_models.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = message.isUser;

    return Padding(
      padding: EdgeInsets.only(
        left: isUser ? 56 : 12,
        right: isUser ? 12 : 56,
        bottom: 10,
      ),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // Avatar + bubble row
          Row(
            mainAxisAlignment:
                isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (!isUser) _avatar(theme),
              if (!isUser) const SizedBox(width: 8),
              Flexible(child: _bubble(context, theme, isUser)),
              if (isUser) const SizedBox(width: 8),
              if (isUser) _userAvatar(theme),
            ],
          ),
          // Citation chips
          if (message.citations.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 6, left: 40),
              child: Wrap(
                spacing: 6,
                runSpacing: 4,
                children: message.citations
                    .map((c) => _CitationChip(citation: c))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _avatar(ThemeData theme) => CircleAvatar(
        radius: 16,
        backgroundColor: theme.colorScheme.primary,
        child: const Icon(Icons.support_agent, size: 18, color: Colors.white),
      );

  Widget _userAvatar(ThemeData theme) => CircleAvatar(
        radius: 16,
        backgroundColor: theme.colorScheme.secondary,
        child: const Icon(Icons.person, size: 18, color: Colors.white),
      );

  Widget _bubble(BuildContext context, ThemeData theme, bool isUser) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isUser
            ? theme.colorScheme.primary
            : theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(16),
          topRight: const Radius.circular(16),
          bottomLeft: Radius.circular(isUser ? 16 : 4),
          bottomRight: Radius.circular(isUser ? 4 : 16),
        ),
      ),
      child: SelectableText(
        message.text,
        style: TextStyle(
          fontSize: 14,
          color: isUser
              ? Colors.white
              : theme.colorScheme.onSurface,
          height: 1.45,
        ),
      ),
    );
  }
}

class _CitationChip extends StatelessWidget {
  final ChatCitation citation;
  const _CitationChip({required this.citation});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Tooltip(
      message: citation.snippet,
      preferBelow: false,
      child: Chip(
        avatar: Icon(Icons.article_outlined,
            size: 14, color: theme.colorScheme.primary),
        label: Text(
          'Page ${citation.page}',
          style: TextStyle(
            fontSize: 11,
            color: theme.colorScheme.primary,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor:
            theme.colorScheme.primary.withValues(alpha: 0.08),
        side: BorderSide(
            color: theme.colorScheme.primary.withValues(alpha: 0.3)),
        padding: EdgeInsets.zero,
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
        visualDensity: VisualDensity.compact,
      ),
    );
  }
}

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl =
      AnimationController(vsync: this, duration: const Duration(milliseconds: 900))
        ..repeat(reverse: true);

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(left: 12, bottom: 10),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: theme.colorScheme.primary,
            child: const Icon(Icons.support_agent, size: 18, color: Colors.white),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomRight: Radius.circular(16),
                bottomLeft: Radius.circular(4),
              ),
            ),
            child: AnimatedBuilder(
              animation: _ctrl,
              builder: (_, __) => Row(
                mainAxisSize: MainAxisSize.min,
                children: List.generate(
                  3,
                  (i) => _Dot(delay: i * 0.25, progress: _ctrl.value),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatelessWidget {
  final double delay;
  final double progress;
  const _Dot({required this.delay, required this.progress});

  @override
  Widget build(BuildContext context) {
    final offset = ((progress + delay) % 1.0);
    final scale = 0.6 + 0.4 * (offset < 0.5 ? offset * 2 : (1 - offset) * 2);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: Transform.scale(
        scale: scale,
        child: CircleAvatar(
          radius: 4,
          backgroundColor: Theme.of(context)
              .colorScheme
              .primary
              .withValues(alpha: 0.7),
        ),
      ),
    );
  }
}
