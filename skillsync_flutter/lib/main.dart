// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'presentation/auth/auth_provider.dart';
import 'router.dart';

void main() {
  runApp(const ProviderScope(child: SkillSyncApp()));
}

class SkillSyncApp extends ConsumerStatefulWidget {
  const SkillSyncApp({super.key});

  @override
  ConsumerState<SkillSyncApp> createState() => _SkillSyncAppState();
}

class _SkillSyncAppState extends ConsumerState<SkillSyncApp> {
  late final _router = buildRouter();

  @override
  Widget build(BuildContext context) {
    final isDark = ref.watch(darkModeProvider);

    return MaterialApp.router(
      title: 'SkillSync HRMS',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: isDark ? ThemeMode.dark : ThemeMode.light,
      routerConfig: _router,
    );
  }
}
