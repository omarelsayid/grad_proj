// lib/presentation/employee/holidays/screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/widgets/loading_view.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/app_date_utils.dart';
import '../../../domain/entities/holiday.dart';
import '../../auth/auth_provider.dart';

final _holidaysProvider = FutureProvider<List<Holiday>>((ref) async {
  return ref.read(skillRepositoryProvider).getHolidays();
});

class EmployeeHolidaysScreen extends ConsumerWidget {
  const EmployeeHolidaysScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final holidaysAsync = ref.watch(_holidaysProvider);

    return holidaysAsync.when(
      loading: () => const LoadingView(),
      error: (e, _) => Center(child: Text('$e')),
      data: (holidays) {
        if (holidays.isEmpty) {
          return const EmptyState(icon: Icons.celebration_outlined, title: 'No holidays scheduled');
        }

        final sorted = List<Holiday>.from(holidays)..sort((a, b) => a.date.compareTo(b.date));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: sorted.length + 1,
          itemBuilder: (ctx, i) {
            if (i == 0) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text('${holidays.length} Holidays in 2026',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              );
            }
            return _HolidayCard(holiday: sorted[i - 1]);
          },
        );
      },
    );
  }
}

class _HolidayCard extends StatelessWidget {
  final Holiday holiday;
  const _HolidayCard({required this.holiday});

  Color get _typeColor {
    switch (holiday.type) {
      case HolidayType.public: return AppColors.riskHigh;
      case HolidayType.company: return AppColors.primary;
      case HolidayType.optional: return AppColors.secondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isPast = holiday.date.isBefore(DateTime.now());
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          width: 48, height: 48,
          decoration: BoxDecoration(
            color: _typeColor.withOpacity(isPast ? 0.07 : 0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(Icons.celebration_outlined, color: isPast ? Colors.grey : _typeColor),
        ),
        title: Text(holiday.name, style: TextStyle(
          fontWeight: FontWeight.w500,
          color: isPast ? Colors.grey : null,
          decoration: isPast ? TextDecoration.lineThrough : null,
        )),
        subtitle: Text(AppDateUtils.formatDate(holiday.date), style: const TextStyle(fontSize: 12)),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: _typeColor.withOpacity(0.12),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(holiday.typeLabel, style: TextStyle(color: _typeColor, fontSize: 11, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }
}
