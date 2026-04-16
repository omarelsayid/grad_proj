// lib/presentation/auth/widgets/login_form.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../domain/entities/employee.dart';
import '../../../services/auth_service.dart';

class LoginForm extends ConsumerStatefulWidget {
  final void Function(Employee, String) onLogin;

  const LoginForm({super.key, required this.onLogin});

  @override
  ConsumerState<LoginForm> createState() => _LoginFormState();
}

class _LoginFormState extends ConsumerState<LoginForm> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  String _selectedRole = 'employee';
  bool _obscure = true;
  bool _loading = false;

  final _demoCredentials = {
    'employee': ('ahmed.hassan@skillsync.dev', 'Employee@123'),
    'manager': ('tarek.mansour@skillsync.dev', 'Manager@123'),
    'hr_admin': ('rana.essam@skillsync.dev', 'Admin@123'),
  };

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final result = await AuthService.instance.login(
        _emailCtrl.text.trim(),
        _passwordCtrl.text,
      );
      widget.onLogin(result.employee, result.role);
    } on Exception catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _fillDemo(String role) {
    final creds = _demoCredentials[role]!;
    _emailCtrl.text = creds.$1;
    _passwordCtrl.text = creds.$2;
    setState(() => _selectedRole = role);
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailCtrl,
            decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined)),
            keyboardType: TextInputType.emailAddress,
            validator: (v) => v != null && v.contains('@') ? null : 'Enter valid email',
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordCtrl,
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline),
              suffixIcon: IconButton(
                icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
            obscureText: _obscure,
            validator: (v) => (v?.length ?? 0) >= 6 ? null : 'Min 6 characters',
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _selectedRole,
            decoration: const InputDecoration(labelText: 'Role', prefixIcon: Icon(Icons.badge_outlined)),
            items: const [
              DropdownMenuItem(value: 'employee', child: Text('Employee')),
              DropdownMenuItem(value: 'manager', child: Text('Manager')),
              DropdownMenuItem(value: 'hr_admin', child: Text('HR Admin')),
            ],
            onChanged: (v) => setState(() => _selectedRole = v!),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loading ? null : _submit,
            child: _loading
                ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Sign In'),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8, alignment: WrapAlignment.center,
            children: ['employee', 'manager', 'hr_admin'].map((r) =>
              ActionChip(
                label: Text('Demo ${r.replaceAll('_', ' ')}'),
                onPressed: () => _fillDemo(r),
              ),
            ).toList(),
          ),
        ],
      ),
    );
  }
}
