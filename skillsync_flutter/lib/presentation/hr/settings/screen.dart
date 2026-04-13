// lib/presentation/hr/settings/screen.dart
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

class HrSettingsScreen extends StatefulWidget {
  const HrSettingsScreen({super.key});
  @override State<HrSettingsScreen> createState() => _State();
}

class _State extends State<HrSettingsScreen> {
  final _companyCtrl = TextEditingController(text: 'SkillSync Technologies');
  final _fiscalCtrl = TextEditingController(text: 'January – December');
  final _annualCtrl = TextEditingController(text: '21');
  final _sickCtrl = TextEditingController(text: '10');
  final _noticeCtrl = TextEditingController(text: '30');
  bool _saved = false;

  @override
  void dispose() {
    _companyCtrl.dispose(); _fiscalCtrl.dispose();
    _annualCtrl.dispose(); _sickCtrl.dispose(); _noticeCtrl.dispose();
    super.dispose();
  }

  void _save() {
    setState(() => _saved = true);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Settings saved successfully.'), backgroundColor: AppColors.success));
  }

  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(16), children: [
      _Section('Company Information', [
        _field(_companyCtrl, 'Company Name', Icons.business_outlined),
        _field(_fiscalCtrl, 'Fiscal Year', Icons.calendar_today_outlined),
      ]),
      const SizedBox(height: 16),
      _Section('Leave Policies', [
        _field(_annualCtrl, 'Annual Leave Days', Icons.beach_access_outlined, number: true),
        _field(_sickCtrl, 'Sick Leave Days', Icons.medical_services_outlined, number: true),
        _field(_noticeCtrl, 'Default Notice Period (days)', Icons.schedule_outlined, number: true),
      ]),
      const SizedBox(height: 16),
      _Section('Notifications', [
        _toggle('Email notifications', Icons.email_outlined, true),
        _toggle('Push notifications', Icons.notifications_outlined, false),
        _toggle('Weekly reports', Icons.analytics_outlined, true),
      ]),
      const SizedBox(height: 24),
      ElevatedButton.icon(onPressed: _save, icon: const Icon(Icons.save), label: const Text('Save Settings')),
    ]);
  }

  Widget _Section(String title, List<Widget> children) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
    const SizedBox(height: 12),
    ...children,
  ])));

  Widget _field(TextEditingController ctrl, String label, IconData icon, {bool number = false}) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextField(controller: ctrl, decoration: InputDecoration(labelText: label, prefixIcon: Icon(icon)), keyboardType: number ? TextInputType.number : TextInputType.text),
  );

  Widget _toggle(String label, IconData icon, bool initial) {
    return StatefulBuilder(builder: (ctx, setS) {
      bool val = initial;
      return SwitchListTile(
        value: val, title: Text(label), secondary: Icon(icon),
        onChanged: (v) => setS(() => val = v),
        contentPadding: EdgeInsets.zero,
      );
    });
  }
}
