// lib/presentation/shell/nav_item.dart
import 'package:flutter/material.dart';

class NavItem {
  final String label;
  final IconData icon;
  final String route;
  /// When set, tapping this item opens the URL externally instead of navigating.
  final String? externalUrl;

  const NavItem({
    required this.label,
    required this.icon,
    required this.route,
    this.externalUrl,
  });

  bool get isExternal => externalUrl != null;
}

final employeeNavItems = <NavItem>[
  const NavItem(label: 'Dashboard', icon: Icons.dashboard_outlined, route: '/employee/dashboard'),
  const NavItem(label: 'Skills', icon: Icons.psychology_outlined, route: '/employee/skills'),
  const NavItem(label: 'Learning', icon: Icons.school_outlined, route: '/employee/learning'),
  const NavItem(label: 'Mobility', icon: Icons.swap_horiz_outlined, route: '/employee/mobility'),
  const NavItem(label: 'Attendance', icon: Icons.calendar_month_outlined, route: '/employee/attendance'),
  const NavItem(label: 'Leaves', icon: Icons.beach_access_outlined, route: '/employee/leaves'),
  const NavItem(label: 'Holidays', icon: Icons.celebration_outlined, route: '/employee/holidays'),
  const NavItem(label: 'Payroll', icon: Icons.payments_outlined, route: '/employee/payroll'),
  const NavItem(label: 'Todos', icon: Icons.checklist_outlined, route: '/employee/todos'),
  const NavItem(label: 'Resignation', icon: Icons.exit_to_app_outlined, route: '/employee/resignation'),
  const NavItem(label: 'Notifications', icon: Icons.notifications_outlined, route: '/employee/notifications'),
  const NavItem(label: 'Chat', icon: Icons.chat_bubble_outline, route: '/employee/chat'),
];

final managerNavItems = <NavItem>[
  const NavItem(label: 'Dashboard', icon: Icons.dashboard_outlined, route: '/manager/dashboard'),
  const NavItem(label: 'Live Analytics', icon: Icons.bar_chart_rounded, route: '/manager/dashboard', externalUrl: 'http://localhost:8502'),
  const NavItem(label: 'Team', icon: Icons.group_outlined, route: '/manager/team'),
  const NavItem(label: 'Departments', icon: Icons.account_tree_outlined, route: '/manager/departments'),
  const NavItem(label: 'Roles', icon: Icons.badge_outlined, route: '/manager/roles'),
  const NavItem(label: 'Skills', icon: Icons.psychology_outlined, route: '/manager/skills'),
  const NavItem(label: 'Learning', icon: Icons.school_outlined, route: '/manager/learning'),
  const NavItem(label: 'Replacements', icon: Icons.people_outlined, route: '/manager/replacements'),
  const NavItem(label: 'Attendance', icon: Icons.calendar_month_outlined, route: '/manager/attendance'),
  const NavItem(label: 'Leaves', icon: Icons.beach_access_outlined, route: '/manager/leaves'),
  const NavItem(label: 'Payroll', icon: Icons.payments_outlined, route: '/manager/payroll'),
  const NavItem(label: 'Todos', icon: Icons.checklist_outlined, route: '/manager/todos'),
  const NavItem(label: 'Notifications', icon: Icons.notifications_outlined, route: '/manager/notifications'),
  const NavItem(label: 'Chat', icon: Icons.chat_bubble_outline, route: '/manager/chat'),
];

final hrNavItems = <NavItem>[
  const NavItem(label: 'Dashboard', icon: Icons.dashboard_outlined, route: '/hr/dashboard'),
  const NavItem(label: 'Live Analytics', icon: Icons.bar_chart_rounded, route: '/hr/dashboard', externalUrl: 'http://localhost:8501'),
  const NavItem(label: 'Employees', icon: Icons.people_outlined, route: '/hr/employees'),
  const NavItem(label: 'Departments', icon: Icons.account_tree_outlined, route: '/hr/departments'),
  const NavItem(label: 'Roles', icon: Icons.badge_outlined, route: '/hr/roles'),
  const NavItem(label: 'Attendance', icon: Icons.calendar_month_outlined, route: '/hr/attendance'),
  const NavItem(label: 'Leaves', icon: Icons.beach_access_outlined, route: '/hr/leaves'),
  const NavItem(label: 'Payroll', icon: Icons.payments_outlined, route: '/hr/payroll'),
  const NavItem(label: 'Resignations', icon: Icons.exit_to_app_outlined, route: '/hr/resignations'),
  const NavItem(label: 'Policies', icon: Icons.policy_outlined, route: '/hr/policies'),
  const NavItem(label: 'Analytics', icon: Icons.analytics_outlined, route: '/hr/analytics'),
  const NavItem(label: 'Turnover', icon: Icons.trending_down_outlined, route: '/hr/turnover'),
  const NavItem(label: 'Audit', icon: Icons.history_outlined, route: '/hr/audit'),
  const NavItem(label: 'Settings', icon: Icons.settings_outlined, route: '/hr/settings'),
  const NavItem(label: 'Notifications', icon: Icons.notifications_outlined, route: '/hr/notifications'),
  const NavItem(label: 'Chat', icon: Icons.chat_bubble_outline, route: '/hr/chat'),
];
