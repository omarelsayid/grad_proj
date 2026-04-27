// lib/presentation/shell/app_shell.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../auth/auth_provider.dart';
import '../hr_buddy/screen.dart';
import 'nav_item.dart';

class AppShell extends ConsumerWidget {
  final Widget child;
  final List<NavItem> navItems;
  final String title;

  const AppShell({
    super.key,
    required this.child,
    required this.navItems,
    required this.title,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final isDark = ref.watch(darkModeProvider);
    final isWide = MediaQuery.of(context).size.width > 720;

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: () => ref.read(darkModeProvider.notifier).state = !isDark,
          ),
          PopupMenuButton<String>(
            icon: CircleAvatar(
              radius: 16,
              child: Text(
                authState.currentUser?.name.isNotEmpty == true
                    ? authState.currentUser!.name.substring(0, 1).toUpperCase()
                    : 'U',
                style: const TextStyle(fontSize: 14),
              ),
            ),
            itemBuilder: (_) => [
              PopupMenuItem(
                value: 'profile',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(authState.currentUser?.name ?? 'User',
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text(authState.currentUser?.email ?? '',
                        style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(value: 'logout', child: Row(
                children: [Icon(Icons.logout, size: 18), SizedBox(width: 8), Text('Logout')],
              )),
            ],
            onSelected: (v) {
              if (v == 'logout') {
                ref.read(authProvider.notifier).logout();
                context.go('/auth');
              }
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      drawer: isWide ? null : _buildDrawer(context),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const HrBuddyChatScreen()),
        ),
        icon: const Icon(Icons.support_agent),
        label: const Text('HR Buddy'),
        tooltip: 'Ask HR policy questions',
      ),
      body: isWide
          ? Row(children: [
              _SidebarNav(navItems: navItems),
              const VerticalDivider(width: 1),
              Expanded(child: child),
            ])
          : child,
    );
  }

  Widget _buildDrawer(BuildContext context) {
    return Drawer(
      child: Column(
        children: [
          const DrawerHeader(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.hub_rounded, size: 48),
                  SizedBox(height: 8),
                  Text('SkillSync', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                ],
              ),
            ),
          ),
          Expanded(
            child: ListView(
              children: navItems.map((item) => Builder(builder: (ctx) => ListTile(
                leading: Icon(item.icon),
                title: Text(item.label),
                trailing: item.isExternal ? const Icon(Icons.open_in_new, size: 14) : null,
                selected: !item.isExternal && GoRouterState.of(ctx).uri.path.startsWith(item.route),
                onTap: () async {
                  Navigator.pop(ctx);
                  if (item.isExternal) {
                    final uri = Uri.parse(item.externalUrl!);
                    if (await canLaunchUrl(uri)) launchUrl(uri, mode: LaunchMode.externalApplication);
                  } else {
                    ctx.go(item.route);
                  }
                },
              ))).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

/// Scrollable, always-visible sidebar for wide screens.
/// Replaces NavigationRail to handle many nav items without overflow.
class _SidebarNav extends StatelessWidget {
  final List<NavItem> navItems;
  const _SidebarNav({required this.navItems});

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouterState.of(context).uri.path;
    final theme = Theme.of(context);

    return SizedBox(
      width: 190,
      child: Column(
        children: [
          // App brand header
          Container(
            height: 56,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(children: [
              Icon(Icons.hub_rounded, size: 22, color: theme.colorScheme.primary),
              const SizedBox(width: 8),
              Text('SkillSync',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: theme.colorScheme.primary)),
            ]),
          ),
          const Divider(height: 1),
          // Scrollable nav items — no overflow
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: navItems.length,
              itemBuilder: (ctx, i) {
                final item = navItems[i];
                final selected = !item.isExternal && currentPath.startsWith(item.route);
                final itemColor = item.isExternal
                    ? const Color(0xFF1e40af)
                    : selected
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  child: Material(
                    color: item.isExternal
                        ? const Color(0xFF1e40af).withValues(alpha: 0.08)
                        : selected
                            ? theme.colorScheme.primary.withValues(alpha: 0.12)
                            : Colors.transparent,
                    borderRadius: BorderRadius.circular(8),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(8),
                      onTap: () async {
                        if (item.isExternal) {
                          final uri = Uri.parse(item.externalUrl!);
                          if (await canLaunchUrl(uri)) {
                            launchUrl(uri, mode: LaunchMode.externalApplication);
                          }
                        } else {
                          context.go(item.route);
                        }
                      },
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
                        child: Row(children: [
                          Icon(item.icon, size: 19, color: itemColor),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              item.label,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                                color: itemColor,
                              ),
                            ),
                          ),
                          if (item.isExternal)
                            Icon(Icons.open_in_new, size: 12, color: itemColor),
                        ]),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
