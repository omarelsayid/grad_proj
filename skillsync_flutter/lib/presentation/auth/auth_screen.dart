// lib/presentation/auth/auth_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../domain/entities/employee.dart';
import 'auth_provider.dart';
import 'widgets/login_form.dart';
import 'widgets/register_form.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _onLogin(Employee employee, String role) {
    ref.read(authProvider.notifier).login(employee, role);
    switch (role) {
      case 'manager':
        context.go('/manager/dashboard');
      case 'hr_admin':
        context.go('/hr/dashboard');
      default:
        context.go('/employee/dashboard');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildLogo(context),
                  const SizedBox(height: 32),
                  _buildTabBar(context),
                  const SizedBox(height: 24),
                  SizedBox(
                    height: 420,
                    child: TabBarView(
                      controller: _tabController,
                      children: [
                        LoginForm(onLogin: _onLogin),
                        const RegisterForm(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo(BuildContext context) {
    return Column(
      children: [
        Icon(Icons.hub_rounded,
            size: 64, color: Theme.of(context).colorScheme.primary),
        const SizedBox(height: 12),
        Text('SkillSync HRMS',
            style: Theme.of(context)
                .textTheme
                .headlineMedium
                ?.copyWith(fontWeight: FontWeight.bold)),
        Text('Skill-driven HR Management',
            style: Theme.of(context)
                .textTheme
                .bodyMedium
                ?.copyWith(color: Colors.grey)),
      ],
    );
  }

  Widget _buildTabBar(BuildContext context) {
    return TabBar(
      controller: _tabController,
      tabs: const [Tab(text: 'Sign In'), Tab(text: 'Sign Up')],
    );
  }
}
