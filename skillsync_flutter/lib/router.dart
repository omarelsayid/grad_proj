// lib/router.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'presentation/auth/auth_screen.dart';
import 'presentation/shell/app_shell.dart';
import 'presentation/shell/nav_item.dart';
// Employee screens
import 'presentation/employee/dashboard/screen.dart';
import 'presentation/employee/skills/screen.dart';
import 'presentation/employee/learning/screen.dart';
import 'presentation/employee/mobility/screen.dart';
import 'presentation/employee/attendance/screen.dart';
import 'presentation/employee/leaves/screen.dart';
import 'presentation/employee/holidays/screen.dart';
import 'presentation/employee/payroll/screen.dart';
import 'presentation/employee/todos/screen.dart';
import 'presentation/employee/resignation/screen.dart';
import 'presentation/employee/notifications/screen.dart';
import 'presentation/employee/chat/screen.dart';
// Manager screens
import 'presentation/manager/dashboard/screen.dart';
import 'presentation/manager/learning/screen.dart';
import 'presentation/manager/team/screen.dart';
import 'presentation/manager/departments/screen.dart';
import 'presentation/manager/roles/screen.dart';
import 'presentation/manager/skills/screen.dart';
import 'presentation/manager/replacements/screen.dart';
import 'presentation/manager/attendance/screen.dart';
import 'presentation/manager/leaves/screen.dart';
import 'presentation/manager/payroll/screen.dart';
import 'presentation/manager/todos/screen.dart';
import 'presentation/manager/notifications/screen.dart';
import 'presentation/manager/chat/screen.dart';
// HR screens
import 'presentation/hr/dashboard/screen.dart';
import 'presentation/hr/employees/screen.dart';
import 'presentation/hr/departments/screen.dart';
import 'presentation/hr/roles/screen.dart';
import 'presentation/hr/attendance/screen.dart';
import 'presentation/hr/leaves/screen.dart';
import 'presentation/hr/payroll/screen.dart';
import 'presentation/hr/resignations/screen.dart';
import 'presentation/hr/policies/screen.dart';
import 'presentation/hr/analytics/screen.dart';
import 'presentation/hr/audit/screen.dart';
import 'presentation/hr/settings/screen.dart';
import 'presentation/hr/notifications/screen.dart';
import 'presentation/hr/chat/screen.dart';
import 'presentation/hr/turnover/screen.dart';

GoRouter buildRouter() => GoRouter(
  initialLocation: '/auth',
  routes: [
    GoRoute(path: '/auth', builder: (_, __) => const AuthScreen()),

    // ── Employee portal ──────────────────────────────────────────────────
    ShellRoute(
      builder: (ctx, state, child) => AppShell(
        child: child, navItems: employeeNavItems, title: _empTitle(state.uri.path),
      ),
      routes: [
        GoRoute(path: '/employee/dashboard', builder: (_, __) => const EmployeeDashboardScreen()),
        GoRoute(path: '/employee/skills', builder: (_, __) => const EmployeeSkillsScreen()),
        GoRoute(path: '/employee/learning', builder: (_, __) => const EmployeeLearningScreen()),
        GoRoute(path: '/employee/mobility', builder: (_, __) => const EmployeeMobilityScreen()),
        GoRoute(path: '/employee/attendance', builder: (_, __) => const EmployeeAttendanceScreen()),
        GoRoute(path: '/employee/leaves', builder: (_, __) => const EmployeeLeavesScreen()),
        GoRoute(path: '/employee/holidays', builder: (_, __) => const EmployeeHolidaysScreen()),
        GoRoute(path: '/employee/payroll', builder: (_, __) => const EmployeePayrollScreen()),
        GoRoute(path: '/employee/todos', builder: (_, __) => const EmployeeTodosScreen()),
        GoRoute(path: '/employee/resignation', builder: (_, __) => const EmployeeResignationScreen()),
        GoRoute(path: '/employee/notifications', builder: (_, __) => const NotificationsScreen()),
        GoRoute(path: '/employee/chat', builder: (_, __) => const EmployeeChatScreen()),
      ],
    ),

    // ── Manager portal ───────────────────────────────────────────────────
    ShellRoute(
      builder: (ctx, state, child) => AppShell(
        child: child, navItems: managerNavItems, title: _mgrTitle(state.uri.path),
      ),
      routes: [
        GoRoute(path: '/manager/dashboard', builder: (_, __) => const ManagerDashboardScreen()),
        GoRoute(path: '/manager/team', builder: (_, __) => const ManagerTeamScreen()),
        GoRoute(path: '/manager/departments', builder: (_, __) => const ManagerDepartmentsScreen()),
        GoRoute(path: '/manager/roles', builder: (_, __) => const ManagerRolesScreen()),
        GoRoute(path: '/manager/skills', builder: (_, __) => const ManagerSkillsScreen()),
        GoRoute(path: '/manager/replacements', builder: (_, __) => const ManagerReplacementsScreen()),
        GoRoute(path: '/manager/attendance', builder: (_, __) => const ManagerAttendanceScreen()),
        GoRoute(path: '/manager/leaves', builder: (_, __) => const ManagerLeavesScreen()),
        GoRoute(path: '/manager/payroll', builder: (_, __) => const ManagerPayrollScreen()),
        GoRoute(path: '/manager/learning', builder: (_, __) => const ManagerTeamLearningScreen()),
        GoRoute(path: '/manager/todos', builder: (_, __) => const ManagerTodosScreen()),
        GoRoute(path: '/manager/notifications', builder: (_, __) => const ManagerNotificationsScreen()),
        GoRoute(path: '/manager/chat', builder: (_, __) => const ManagerChatScreen()),
      ],
    ),

    // ── HR Admin portal ──────────────────────────────────────────────────
    ShellRoute(
      builder: (ctx, state, child) => AppShell(
        child: child, navItems: hrNavItems, title: _hrTitle(state.uri.path),
      ),
      routes: [
        GoRoute(path: '/hr/dashboard', builder: (_, __) => const HrDashboardScreen()),
        GoRoute(path: '/hr/employees', builder: (_, __) => const HrEmployeesScreen()),
        GoRoute(path: '/hr/departments', builder: (_, __) => const HrDepartmentsScreen()),
        GoRoute(path: '/hr/roles', builder: (_, __) => const HrRolesScreen()),
        GoRoute(path: '/hr/attendance', builder: (_, __) => const HrAttendanceScreen()),
        GoRoute(path: '/hr/leaves', builder: (_, __) => const HrLeavesScreen()),
        GoRoute(path: '/hr/payroll', builder: (_, __) => const HrPayrollScreen()),
        GoRoute(path: '/hr/resignations', builder: (_, __) => const HrResignationsScreen()),
        GoRoute(path: '/hr/policies', builder: (_, __) => const HrPoliciesScreen()),
        GoRoute(path: '/hr/analytics', builder: (_, __) => const HrAnalyticsScreen()),
        GoRoute(path: '/hr/turnover', builder: (_, __) => const HrTurnoverScreen()),
        GoRoute(path: '/hr/audit', builder: (_, __) => const HrAuditScreen()),
        GoRoute(path: '/hr/settings', builder: (_, __) => const HrSettingsScreen()),
        GoRoute(path: '/hr/notifications', builder: (_, __) => const HrNotificationsScreen()),
        GoRoute(path: '/hr/chat', builder: (_, __) => const HrChatScreen()),
      ],
    ),
  ],
);

String _empTitle(String path) {
  final map = {
    'dashboard': 'Dashboard', 'skills': 'My Skills', 'learning': 'Learning Path',
    'mobility': 'Internal Mobility', 'attendance': 'Attendance', 'leaves': 'Leaves',
    'holidays': 'Holidays', 'payroll': 'Payroll', 'todos': 'Tasks',
    'resignation': 'Resignation', 'notifications': 'Notifications', 'chat': 'AI HR Chat',
  };
  final seg = path.split('/').last;
  return map[seg] ?? 'SkillSync';
}

String _mgrTitle(String path) {
  final map = {
    'dashboard': 'Team Overview', 'team': 'My Team', 'departments': 'Team Departments',
    'roles': 'Open Roles', 'skills': 'Team Skills',
    'learning': 'Team Learning', 'replacements': 'Replacement Planning', 'attendance': 'Team Attendance',
    'leaves': 'Leave Requests', 'payroll': 'Team Payroll', 'todos': 'Tasks',
    'notifications': 'Notifications', 'chat': 'AI HR Chat',
  };
  final seg = path.split('/').last;
  return map[seg] ?? 'SkillSync';
}

String _hrTitle(String path) {
  final map = {
    'dashboard': 'HR Dashboard', 'employees': 'Employee Directory', 'departments': 'Departments',
    'roles': 'Job Roles', 'attendance': 'Org Attendance', 'leaves': 'All Leaves',
    'payroll': 'Org Payroll', 'resignations': 'Resignations', 'policies': 'Policies',
    'analytics': 'Analytics', 'turnover': 'Turnover Prediction', 'audit': 'Audit Log',
    'settings': 'Settings', 'notifications': 'Notifications', 'chat': 'AI HR Chat',
  };
  final seg = path.split('/').last;
  return map[seg] ?? 'SkillSync';
}
