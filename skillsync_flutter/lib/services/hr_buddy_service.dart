// lib/services/hr_buddy_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/chat_models.dart';

class HrBuddyService {
  // Change this to your backend host when deploying.
  static const String _baseUrl = 'http://localhost:8001';

  static final HrBuddyService _instance = HrBuddyService._();
  factory HrBuddyService() => _instance;
  HrBuddyService._();

  Future<bool> isReady() async {
    try {
      final resp = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        return data['index_ready'] as bool? ?? false;
      }
    } catch (_) {}
    return false;
  }

  Future<void> ingestPdf() async {
    final resp = await http
        .post(Uri.parse('$_baseUrl/ingest-pdf'))
        .timeout(const Duration(minutes: 5));
    if (resp.statusCode != 200) {
      throw Exception('Ingest failed: ${resp.body}');
    }
  }

  Future<ChatResponse> sendMessage(String message, {String? sessionId}) async {
    final body = jsonEncode({
      'message': message,
      if (sessionId != null) 'session_id': sessionId,
    });

    final resp = await http
        .post(
          Uri.parse('$_baseUrl/chat'),
          headers: {'Content-Type': 'application/json'},
          body: body,
        )
        .timeout(const Duration(seconds: 30));

    if (resp.statusCode == 200) {
      return ChatResponse.fromJson(
          jsonDecode(resp.body) as Map<String, dynamic>);
    }
    throw Exception('Chat error (${resp.statusCode}): ${resp.body}');
  }
}
