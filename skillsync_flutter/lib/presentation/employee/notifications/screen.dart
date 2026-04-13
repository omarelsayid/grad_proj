// lib/presentation/employee/notifications/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/app_notification.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

class NotificationsScreen extends ConsumerStatefulWidget {
  const NotificationsScreen({super.key});
  @override ConsumerState<NotificationsScreen> createState() => _State();
}

class _State extends ConsumerState<NotificationsScreen> {
  List<AppNotification> _notifications = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null) { setState(() => _loading = false); return; }
    final list = await ref.read(employeeRepositoryProvider).getNotifications(emp.id);
    if (mounted) setState(() { _notifications = list.toList(); _loading = false; });
  }

  Future<void> _markRead(AppNotification n) async {
    if (n.isRead) return;
    await ref.read(employeeRepositoryProvider).markNotificationRead(n.id);
    setState(() {
      final i = _notifications.indexWhere((x) => x.id == n.id);
      if (i != -1) _notifications[i] = n.copyWith(isRead: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();

    final unread = _notifications.where((n) => !n.isRead).length;

    return Scaffold(
      body: _notifications.isEmpty
          ? const EmptyState(icon: Icons.notifications_none, title: 'No notifications')
          : Column(children: [
              if (unread > 0)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  color: AppColors.primary.withOpacity(0.05),
                  child: Text('$unread unread notification${unread > 1 ? 's' : ''}', style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w500)),
                ),
              Expanded(child: ListView.builder(
                itemCount: _notifications.length,
                itemBuilder: (ctx, i) {
                  final n = _notifications[i];
                  return _NotificationTile(notification: n, onTap: () => _markRead(n));
                },
              )),
            ]),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final AppNotification notification;
  final VoidCallback onTap;
  const _NotificationTile({required this.notification, required this.onTap});

  IconData get _icon {
    switch (notification.type) {
      case 'success': return Icons.check_circle_outline;
      case 'warning': return Icons.warning_amber_outlined;
      case 'leave': return Icons.beach_access_outlined;
      case 'payroll': return Icons.payments_outlined;
      default: return Icons.info_outline;
    }
  }

  Color get _iconColor {
    switch (notification.type) {
      case 'success': return AppColors.success;
      case 'warning': return AppColors.warning;
      case 'leave': return AppColors.secondary;
      case 'payroll': return AppColors.primary;
      default: return AppColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: notification.isRead ? null : AppColors.primary.withOpacity(0.04),
          border: Border(bottom: BorderSide(color: Colors.grey.withOpacity(0.15))),
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: _iconColor.withOpacity(0.12), shape: BoxShape.circle),
            child: Icon(_icon, color: _iconColor, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(child: Text(notification.title, style: TextStyle(fontWeight: notification.isRead ? FontWeight.normal : FontWeight.bold))),
              if (!notification.isRead) Container(width: 8, height: 8, decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle)),
            ]),
            const SizedBox(height: 4),
            Text(notification.message, style: const TextStyle(fontSize: 13, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(AppDateUtils.timeAgo(notification.createdAt), style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ])),
        ]),
      ),
    );
  }
}
