// lib/presentation/hr_buddy/screen.dart
import 'package:flutter/material.dart';
import '../../models/chat_models.dart';
import '../../services/hr_buddy_service.dart';
import '../../widgets/chat_bubble.dart';

const _suggestedQuestions = [
  'How many annual leave days do I get?',
  'What is the resignation notice period?',
  'What are skill chains?',
  'How do I access learning resources?',
  'What happens if I am late to work?',
  'What are the criticality tiers for skill gaps?',
];

class HrBuddyChatScreen extends StatefulWidget {
  const HrBuddyChatScreen({super.key});

  @override
  State<HrBuddyChatScreen> createState() => _HrBuddyChatScreenState();
}

class _HrBuddyChatScreenState extends State<HrBuddyChatScreen> {
  final _service = HrBuddyService();
  final _messages = <ChatMessage>[];
  final _controller = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _isLoading = false;
  bool _isIndexReady = false;
  bool _checkingIndex = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _checkIndex();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _checkIndex() async {
    final ready = await _service.isReady();
    if (mounted) {
      setState(() {
        _isIndexReady = ready;
        _checkingIndex = false;
      });
      if (!ready) _showNotReadyBanner();
    }
  }

  void _showNotReadyBanner() {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
            'HR Buddy index not ready. Tap "Ingest PDF" to build it first.'),
        action: SnackBarAction(
          label: 'Ingest PDF',
          onPressed: _ingestPdf,
        ),
        duration: const Duration(seconds: 6),
      ),
    );
  }

  Future<void> _ingestPdf() async {
    setState(() => _isLoading = true);
    try {
      await _service.ingestPdf();
      if (mounted) {
        setState(() => _isIndexReady = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('PDF indexed successfully!'),
              backgroundColor: Colors.green),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = e.toString());
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _send(String text) async {
    text = text.trim();
    if (text.isEmpty || _isLoading) return;

    _controller.clear();
    setState(() {
      _messages.add(ChatMessage(
          text: text, isUser: true, timestamp: DateTime.now()));
      _isLoading = true;
      _error = null;
    });
    _scrollToBottom();

    try {
      final resp = await _service.sendMessage(text);
      if (mounted) {
        setState(() {
          _messages.add(ChatMessage(
            text: resp.answer,
            isUser: false,
            citations: resp.citations,
            timestamp: DateTime.now(),
          ));
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Could not reach HR Buddy backend. '
            'Make sure the server is running on port 8001.');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: theme.colorScheme.primary,
              child: const Icon(Icons.support_agent, size: 18, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('HR Buddy',
                    style:
                        TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                Text(
                  _isIndexReady ? 'Online · Policy grounded' : 'Index not ready',
                  style: TextStyle(
                    fontSize: 11,
                    color: _isIndexReady ? Colors.green : Colors.orange,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          if (!_isIndexReady && !_checkingIndex)
            TextButton.icon(
              onPressed: _isLoading ? null : _ingestPdf,
              icon: const Icon(Icons.upload_file, size: 16),
              label: const Text('Ingest PDF', style: TextStyle(fontSize: 12)),
            ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          if (_error != null) _ErrorBanner(message: _error!),
          Expanded(
            child: _messages.isEmpty
                ? _WelcomeView(onSuggestion: _send, isReady: _isIndexReady)
                : ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    itemCount: _messages.length + (_isLoading ? 1 : 0),
                    itemBuilder: (_, i) {
                      if (i == _messages.length) {
                        return const TypingIndicator();
                      }
                      return ChatBubble(message: _messages[i]);
                    },
                  ),
          ),
          _InputBar(
            controller: _controller,
            isLoading: _isLoading,
            onSend: _send,
          ),
        ],
      ),
    );
  }
}

// ── sub-widgets ─────────────────────────────────────────────────────────────

class _WelcomeView extends StatelessWidget {
  final void Function(String) onSuggestion;
  final bool isReady;
  const _WelcomeView({required this.onSuggestion, required this.isReady});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const SizedBox(height: 16),
          CircleAvatar(
            radius: 36,
            backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.12),
            child: Icon(Icons.support_agent,
                size: 42, color: theme.colorScheme.primary),
          ),
          const SizedBox(height: 16),
          Text('Hi! I\'m HR Buddy',
              style: theme.textTheme.titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(
            'I answer questions about SkillSync company policies.\n'
            'Every answer is grounded in the official HR policy document.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
          if (!isReady) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.withValues(alpha: 0.3)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.warning_amber, color: Colors.orange, size: 16),
                  SizedBox(width: 8),
                  Text('Backend index not ready. Tap "Ingest PDF" above.',
                      style: TextStyle(fontSize: 12, color: Colors.orange)),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          Text('Try asking:',
              style: theme.textTheme.labelLarge
                  ?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 12),
          ..._suggestedQuestions.map(
            (q) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: () => onSuggestion(q),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border.all(
                        color: theme.colorScheme.outline.withValues(alpha: 0.4)),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.chat_bubble_outline,
                          size: 16, color: theme.colorScheme.primary),
                      const SizedBox(width: 10),
                      Expanded(
                          child: Text(q,
                              style: const TextStyle(fontSize: 13))),
                      Icon(Icons.arrow_forward_ios,
                          size: 12,
                          color: theme.colorScheme.onSurfaceVariant),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool isLoading;
  final void Function(String) onSend;

  const _InputBar(
      {required this.controller,
      required this.isLoading,
      required this.onSend});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(top: BorderSide(color: theme.colorScheme.outlineVariant)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: isLoading ? null : onSend,
              decoration: InputDecoration(
                hintText: 'Ask about company policy…',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: theme.colorScheme.surfaceContainerHighest,
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
            ),
          ),
          const SizedBox(width: 8),
          FilledButton(
            onPressed: isLoading ? null : () => onSend(controller.text),
            style: FilledButton.styleFrom(
              shape: const CircleBorder(),
              padding: const EdgeInsets.all(12),
            ),
            child: isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.send_rounded, size: 20),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: Colors.red.withValues(alpha: 0.1),
      child: Row(
        children: [
          const Icon(Icons.error_outline, size: 16, color: Colors.red),
          const SizedBox(width: 8),
          Expanded(
              child: Text(message,
                  style: const TextStyle(fontSize: 12, color: Colors.red))),
        ],
      ),
    );
  }
}
