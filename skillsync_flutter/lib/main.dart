// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'presentation/auth/auth_provider.dart';
import 'router.dart';

void main() {
  runApp(const ProviderScope(child: SkillSyncApp()));
}

class SkillSyncApp extends ConsumerWidget {
  const SkillSyncApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = ref.watch(darkModeProvider);
    final router = buildRouter();

    return MaterialApp.router(
      title: 'SkillSync HRMS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: isDark ? ThemeMode.dark : ThemeMode.light,
      routerConfig: router,
    );
  }
}
