// lib/presentation/hr/policies/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/theme/app_colors.dart';
import '../../../domain/entities/skill.dart';
import '../../../domain/entities/role.dart';
import '../../../domain/entities/learning_item.dart';
import '../../auth/auth_provider.dart';
import '../../employee/dashboard/provider.dart';
import '../../employee/learning/screen.dart';

class HrPoliciesScreen extends ConsumerStatefulWidget {
  const HrPoliciesScreen({super.key});
  @override ConsumerState<HrPoliciesScreen> createState() => _State();
}

class _State extends ConsumerState<HrPoliciesScreen> with SingleTickerProviderStateMixin {
  late TabController _tabs;

  @override
  void initState() { super.initState(); _tabs = TabController(length: 3, vsync: this); }
  @override
  void dispose() { _tabs.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      TabBar(controller: _tabs, tabs: const [Tab(text: 'Skills'), Tab(text: 'Roles'), Tab(text: 'Learning')]),
      Expanded(child: TabBarView(controller: _tabs, children: [
        _SkillsTab(),
        _RolesTab(),
        _LearningTab(),
      ])),
    ]);
  }
}

class _SkillsTab extends ConsumerStatefulWidget {
  @override ConsumerState<_SkillsTab> createState() => _SkillsTabState();
}

class _SkillsTabState extends ConsumerState<_SkillsTab> {
  List<Skill> _skills = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final list = await ref.read(skillRepositoryProvider).getAllSkills();
    if (mounted) setState(() { _skills = list.toList(); _loading = false; });
  }

  void _delete(Skill s) async {
    await ref.read(skillRepositoryProvider).deleteSkill(s.id);
    setState(() => _skills.removeWhere((x) => x.id == s.id));
    ref.invalidate(employeeSkillsProvider);
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${s.name} deleted')));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView();
    return Scaffold(
      body: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: _skills.length,
        itemBuilder: (ctx, i) => ListTile(
          title: Text(_skills[i].name),
          subtitle: Text(_skills[i].category.name),
          trailing: IconButton(icon: const Icon(Icons.delete_outline, size: 18), onPressed: () => _delete(_skills[i])),
        ),
      ),
      floatingActionButton: FloatingActionButton.small(onPressed: () => _showAddDialog(context), child: const Icon(Icons.add)),
    );
  }

  void _showAddDialog(BuildContext context) {
    final nameCtrl = TextEditingController();
    var category = SkillCategory.technical;
    showDialog(context: context, builder: (ctx) => StatefulBuilder(
      builder: (ctx, setS) => AlertDialog(
        title: const Text('Add Skill'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Skill Name')),
          const SizedBox(height: 8),
          DropdownButtonFormField<SkillCategory>(
            value: category, decoration: const InputDecoration(labelText: 'Category'),
            items: SkillCategory.values.map((c) => DropdownMenuItem(value: c, child: Text(c.name))).toList(),
            onChanged: (v) => setS(() => category = v!),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(onPressed: () async {
            final skill = Skill(id: 'sk_${DateTime.now().millisecondsSinceEpoch}', name: nameCtrl.text.trim(), category: category, description: '');
            await ref.read(skillRepositoryProvider).addSkill(skill);
            ref.invalidate(employeeSkillsProvider);
            Navigator.pop(ctx);
            _load();
          }, child: const Text('Add')),
        ],
      ),
    ));
  }
}

class _RolesTab extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rolesAsync = ref.watch(employeeRolesProvider);
    return rolesAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (roles) => ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: (roles as List<Role>).length,
        itemBuilder: (ctx, i) {
          final role = roles[i];
          return ListTile(
            title: Text(role.title),
            subtitle: Text('${role.department} • ${role.levelLabel}'),
            trailing: IconButton(icon: const Icon(Icons.delete_outline, size: 18), onPressed: () async {
              await ref.read(skillRepositoryProvider).deleteRole(role.id);
              ref.invalidate(employeeRolesProvider);
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${role.title} deleted')));
            }),
          );
        },
      ),
    );
  }
}

class _LearningTab extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemsAsync = ref.watch(learningItemsProvider);
    return itemsAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (items) => ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: (items as List<LearningItem>).length,
        itemBuilder: (ctx, i) {
          final item = items[i];
          return ListTile(
            title: Text(item.title),
            subtitle: Text('${item.typeLabel} • ${item.duration}'),
            trailing: IconButton(icon: const Icon(Icons.delete_outline, size: 18), onPressed: () async {
              await ref.read(skillRepositoryProvider).deleteLearningItem(item.id);
              ref.invalidate(learningItemsProvider);
              if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${item.title} deleted')));
            }),
          );
        },
      ),
    );
  }
}
