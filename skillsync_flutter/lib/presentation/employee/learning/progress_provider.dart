// lib/presentation/employee/learning/progress_provider.dart
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../domain/entities/learning_progress.dart';

class LearningProgressNotifier
    extends StateNotifier<Map<String, LearningStatus>> {
  LearningProgressNotifier() : super({}) {
    _load();
  }

  static const _key = 'learning_progress';

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return;
    final map = json.decode(raw) as Map<String, dynamic>;
    state = map.map((k, v) => MapEntry(
          k,
          LearningStatus.values.firstWhere(
            (e) => e.name == v,
            orElse: () => LearningStatus.notStarted,
          ),
        ));
  }

  Future<void> setStatus(String itemId, LearningStatus status) async {
    final next = {...state, itemId: status};
    state = next;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
        _key, json.encode(next.map((k, v) => MapEntry(k, v.name))));
  }

  LearningStatus statusOf(String itemId) =>
      state[itemId] ?? LearningStatus.notStarted;
}

final learningProgressProvider =
    StateNotifierProvider<LearningProgressNotifier, Map<String, LearningStatus>>(
  (ref) => LearningProgressNotifier(),
);
