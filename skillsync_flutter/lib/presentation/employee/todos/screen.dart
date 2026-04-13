// lib/presentation/employee/todos/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/todo.dart';
import '../../auth/auth_provider.dart';
import '../dashboard/provider.dart';

class EmployeeTodosScreen extends ConsumerStatefulWidget {
  const EmployeeTodosScreen({super.key});
  @override ConsumerState<EmployeeTodosScreen> createState() => _State();
}

class _State extends ConsumerState<EmployeeTodosScreen> {
  List<Todo> _todos = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final emp = ref.read(authProvider).currentUser;
    if (emp == null) { setState(() => _loading = false); return; }
    final todos = await ref.read(employeeRepositoryProvider).getTodos(emp.id);
    if (mounted) setState(() { _todos = todos.toList(); _loading = false; });
  }

  Future<void> _toggle(Todo todo) async {
    final updated = todo.copyWith(completed: !todo.completed);
    await ref.read(employeeRepositoryProvider).updateTodo(updated);
    setState(() { final i = _todos.indexWhere((t) => t.id == todo.id); if (i != -1) _todos[i] = updated; });
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(updated.completed ? 'Task completed!' : 'Task reopened')));
  }

  Future<void> _delete(String id) async {
    await ref.read(employeeRepositoryProvider).deleteTodo(id);
    setState(() => _todos.removeWhere((t) => t.id == id));
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Task deleted')));
  }

  void _showAddDialog() {
    final titleCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    var priority = TodoPriority.medium;
    var dueDate = DateTime.now().add(const Duration(days: 7));

    showDialog(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, setS) => AlertDialog(
        title: const Text('New Task'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: titleCtrl, decoration: const InputDecoration(labelText: 'Title')),
          const SizedBox(height: 8),
          TextField(controller: descCtrl, decoration: const InputDecoration(labelText: 'Description'), maxLines: 2),
          const SizedBox(height: 8),
          DropdownButtonFormField<TodoPriority>(
            value: priority,
            decoration: const InputDecoration(labelText: 'Priority'),
            items: TodoPriority.values.map((p) => DropdownMenuItem(value: p, child: Text(p.name.toUpperCase()))).toList(),
            onChanged: (v) => setS(() => priority = v!),
          ),
        ])),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(onPressed: () async {
            final emp = ref.read(authProvider).currentUser;
            if (emp == null || titleCtrl.text.trim().isEmpty) return;
            final todo = Todo(
              id: 'todo_${DateTime.now().millisecondsSinceEpoch}',
              employeeId: emp.id, title: titleCtrl.text.trim(),
              description: descCtrl.text.trim(), dueDate: dueDate,
              priority: priority, completed: false,
            );
            await ref.read(employeeRepositoryProvider).addTodo(todo);
            Navigator.pop(ctx);
            _load();
          }, child: const Text('Add')),
        ],
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();

    final open = _todos.where((t) => !t.completed).toList();
    final done = _todos.where((t) => t.completed).toList();

    return Scaffold(
      body: _todos.isEmpty
          ? EmptyState(icon: Icons.checklist_outlined, title: 'No tasks yet', actionLabel: 'Add Task', onAction: _showAddDialog)
          : ListView(padding: const EdgeInsets.all(16), children: [
              if (open.isNotEmpty) ...[
                Text('Open (${open.length})', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ...open.map((t) => _TodoCard(todo: t, onToggle: () => _toggle(t), onDelete: () => _delete(t.id))),
              ],
              if (done.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text('Completed (${done.length})', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                ...done.map((t) => _TodoCard(todo: t, onToggle: () => _toggle(t), onDelete: () => _delete(t.id))),
              ],
            ]),
      floatingActionButton: FloatingActionButton(onPressed: _showAddDialog, child: const Icon(Icons.add)),
    );
  }
}

class _TodoCard extends StatelessWidget {
  final Todo todo;
  final VoidCallback onToggle, onDelete;
  const _TodoCard({required this.todo, required this.onToggle, required this.onDelete});

  Color get _priorityColor {
    switch (todo.priority) {
      case TodoPriority.high: return AppColors.riskHigh;
      case TodoPriority.medium: return AppColors.warning;
      case TodoPriority.low: return AppColors.success;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Checkbox(value: todo.completed, onChanged: (_) => onToggle(), activeColor: AppColors.primary),
        title: Text(todo.title, style: TextStyle(decoration: todo.completed ? TextDecoration.lineThrough : null, color: todo.completed ? Colors.grey : null)),
        subtitle: Row(children: [
          Container(width: 8, height: 8, decoration: BoxDecoration(color: _priorityColor, shape: BoxShape.circle)),
          const SizedBox(width: 4),
          Text('${todo.priority.name} • Due ${AppDateUtils.formatDate(todo.dueDate)}', style: const TextStyle(fontSize: 11)),
        ]),
        trailing: IconButton(icon: const Icon(Icons.delete_outline, size: 18), onPressed: onDelete),
      ),
    );
  }
}
