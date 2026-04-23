// lib/models/chat_models.dart

class ChatCitation {
  final int page;
  final String snippet;

  const ChatCitation({required this.page, required this.snippet});

  factory ChatCitation.fromJson(Map<String, dynamic> j) =>
      ChatCitation(page: j['page'] as int, snippet: j['snippet'] as String);
}

class ChatMessage {
  final String text;
  final bool isUser;
  final List<ChatCitation> citations;
  final DateTime timestamp;

  const ChatMessage({
    required this.text,
    required this.isUser,
    this.citations = const [],
    required this.timestamp,
  });
}

class ChatResponse {
  final String answer;
  final List<ChatCitation> citations;

  const ChatResponse({required this.answer, required this.citations});

  factory ChatResponse.fromJson(Map<String, dynamic> j) => ChatResponse(
        answer: j['answer'] as String,
        citations: (j['citations'] as List<dynamic>? ?? [])
            .map((e) => ChatCitation.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
