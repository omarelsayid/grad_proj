// lib/data/mock/mock_static_data.dart
import '../../domain/entities/holiday.dart';
import '../../domain/entities/leave_balance.dart';
import '../../domain/entities/leave_request.dart';
import '../../domain/entities/payroll_record.dart';
import '../../domain/entities/todo.dart';
import '../../domain/entities/app_notification.dart';
import '../../domain/entities/resignation_request.dart';
import '../../domain/entities/audit_log.dart';

final mockHolidays = <Holiday>[
  Holiday(id: 'h01', name: 'New Year\'s Day', date: DateTime(2026, 1, 1), type: HolidayType.public),
  Holiday(id: 'h02', name: 'Revolution Day (25 Jan)', date: DateTime(2026, 1, 25), type: HolidayType.public),
  Holiday(id: 'h03', name: 'Eid Al-Fitr', date: DateTime(2026, 3, 20), type: HolidayType.public),
  Holiday(id: 'h04', name: 'Sinai Liberation Day', date: DateTime(2026, 4, 25), type: HolidayType.public),
  Holiday(id: 'h05', name: 'Labor Day', date: DateTime(2026, 5, 1), type: HolidayType.public),
  Holiday(id: 'h06', name: 'Eid Al-Adha', date: DateTime(2026, 5, 27), type: HolidayType.public),
  Holiday(id: 'h07', name: 'Revolution Day (30 Jun)', date: DateTime(2026, 6, 30), type: HolidayType.public),
  Holiday(id: 'h08', name: 'Revolution Day (23 Jul)', date: DateTime(2026, 7, 23), type: HolidayType.public),
  Holiday(id: 'h09', name: 'National Day', date: DateTime(2026, 10, 6), type: HolidayType.public),
  Holiday(id: 'h10', name: 'Company Anniversary', date: DateTime(2026, 9, 15), type: HolidayType.company),
  Holiday(id: 'h11', name: 'Founders Day', date: DateTime(2026, 11, 20), type: HolidayType.company),
  Holiday(id: 'h12', name: 'Volunteer Day', date: DateTime(2026, 12, 5), type: HolidayType.optional),
];

LeaveBalance getLeaveBalance(String employeeId) => LeaveBalance(
      employeeId: employeeId,
      annualTotal: 21,
      annualUsed: employeeId.hashCode.abs() % 10,
      sickTotal: 10,
      sickUsed: employeeId.hashCode.abs() % 4,
      compassionateTotal: 5,
      compassionateUsed: 0,
    );

final mockLeaveRequests = <LeaveRequest>[
  LeaveRequest(id: 'lr01', employeeId: 'emp01', leaveType: 'annual',
      startDate: DateTime(2026, 2, 10), endDate: DateTime(2026, 2, 12),
      reason: 'Family trip', status: LeaveStatus.approved),
  LeaveRequest(id: 'lr02', employeeId: 'emp01', leaveType: 'sick',
      startDate: DateTime(2026, 3, 5), endDate: DateTime(2026, 3, 5),
      reason: 'Medical appointment', status: LeaveStatus.approved),
  LeaveRequest(id: 'lr03', employeeId: 'emp02', leaveType: 'annual',
      startDate: DateTime(2026, 4, 14), endDate: DateTime(2026, 4, 16),
      reason: 'Personal matters', status: LeaveStatus.pending),
  LeaveRequest(id: 'lr04', employeeId: 'emp03', leaveType: 'sick',
      startDate: DateTime(2026, 3, 20), endDate: DateTime(2026, 3, 21),
      reason: 'Flu', status: LeaveStatus.approved),
  LeaveRequest(id: 'lr05', employeeId: 'emp05', leaveType: 'annual',
      startDate: DateTime(2026, 5, 1), endDate: DateTime(2026, 5, 3),
      reason: 'Vacation', status: LeaveStatus.pending),
  LeaveRequest(id: 'lr06', employeeId: 'emp07', leaveType: 'compassionate',
      startDate: DateTime(2026, 2, 22), endDate: DateTime(2026, 2, 24),
      reason: 'Family emergency', status: LeaveStatus.approved),
  LeaveRequest(id: 'lr07', employeeId: 'emp09', leaveType: 'annual',
      startDate: DateTime(2026, 4, 20), endDate: DateTime(2026, 4, 22),
      reason: 'Travel', status: LeaveStatus.rejected),
  LeaveRequest(id: 'lr08', employeeId: 'emp11', leaveType: 'annual',
      startDate: DateTime(2026, 6, 1), endDate: DateTime(2026, 6, 5),
      reason: 'Holiday abroad', status: LeaveStatus.pending),
];

List<PayrollRecord> getPayrollForEmployee(String employeeId, double salary) {
  return List.generate(6, (i) {
    final month = 12 - i;
    final year = month <= 0 ? 2025 : 2026;
    final m = month <= 0 ? month + 12 : month;
    return PayrollRecord(
      id: '${employeeId}_pay_$i',
      employeeId: employeeId,
      month: m,
      year: year,
      basicSalary: salary,
      allowances: salary * 0.15,
      deductions: salary * 0.08,
      status: i == 0 ? PayrollStatus.pending : PayrollStatus.paid,
    );
  });
}

List<Todo> getInitialTodos(String employeeId) => [
  Todo(id: '${employeeId}_t1', employeeId: employeeId,
      title: 'Complete Q2 Performance Review',
      description: 'Fill in self-assessment form before deadline.',
      dueDate: DateTime(2026, 4, 30), priority: TodoPriority.high, completed: false),
  Todo(id: '${employeeId}_t2', employeeId: employeeId,
      title: 'Update skills profile',
      description: 'Add new certifications to your skills list.',
      dueDate: DateTime(2026, 5, 15), priority: TodoPriority.medium, completed: false),
  Todo(id: '${employeeId}_t3', employeeId: employeeId,
      title: 'Team retrospective preparation',
      description: 'Prepare talking points for monthly retro meeting.',
      dueDate: DateTime(2026, 4, 28), priority: TodoPriority.medium, completed: true),
  Todo(id: '${employeeId}_t4', employeeId: employeeId,
      title: 'Submit expense report',
      description: 'Submit March training expenses for reimbursement.',
      dueDate: DateTime(2026, 4, 20), priority: TodoPriority.low, completed: true),
];

List<AppNotification> getNotificationsForUser(String userId) => [
  AppNotification(id: '${userId}_n1', userId: userId,
      title: 'Leave Request Approved',
      message: 'Your annual leave request for Feb 10-12 has been approved.',
      type: 'success', isRead: false,
      createdAt: DateTime(2026, 4, 10, 9, 30)),
  AppNotification(id: '${userId}_n2', userId: userId,
      title: 'Payroll Processed',
      message: 'Your March payroll has been processed and will be paid on April 1st.',
      type: 'info', isRead: false,
      createdAt: DateTime(2026, 4, 9, 14, 0)),
  AppNotification(id: '${userId}_n3', userId: userId,
      title: 'Skill Assessment Due',
      message: 'Your quarterly skill assessment is due by April 30th.',
      type: 'warning', isRead: true,
      createdAt: DateTime(2026, 4, 8, 10, 0)),
  AppNotification(id: '${userId}_n4', userId: userId,
      title: 'New Learning Recommendation',
      message: 'We found a new course matching your development goals.',
      type: 'info', isRead: true,
      createdAt: DateTime(2026, 4, 7, 11, 15)),
  AppNotification(id: '${userId}_n5', userId: userId,
      title: 'Holiday Reminder',
      message: 'Sinai Liberation Day holiday on April 25th — offices closed.',
      type: 'info', isRead: true,
      createdAt: DateTime(2026, 4, 6, 8, 0)),
];

final mockResignations = <ResignationRequest>[
  ResignationRequest(id: 'res01', employeeId: 'emp07',
      lastWorkingDate: DateTime(2026, 5, 31), noticePeriodDays: 30,
      reason: 'Pursuing higher studies abroad.',
      status: ResignationStatus.pending, submittedAt: DateTime(2026, 4, 1)),
  ResignationRequest(id: 'res02', employeeId: 'emp20',
      lastWorkingDate: DateTime(2026, 4, 30), noticePeriodDays: 14,
      reason: 'Personal reasons.',
      status: ResignationStatus.approved, submittedAt: DateTime(2026, 3, 15)),
];

final mockAuditLogs = <AuditLog>[
  AuditLog(id: 'al01', action: 'LEAVE_APPROVE', entityType: 'LeaveRequest',
      entityId: 'lr01', performedBy: 'Tarek Mansour',
      timestamp: DateTime(2026, 4, 10, 9, 0), details: {'employeeId': 'emp01'}),
  AuditLog(id: 'al02', action: 'EMPLOYEE_UPDATE', entityType: 'Employee',
      entityId: 'emp05', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 4, 9, 14, 30), details: {'field': 'salary'}),
  AuditLog(id: 'al03', action: 'PAYROLL_PROCESS', entityType: 'Payroll',
      entityId: 'batch_march', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 4, 1, 8, 0), details: {'month': 'March 2026'}),
  AuditLog(id: 'al04', action: 'RESIGNATION_APPROVE', entityType: 'ResignationRequest',
      entityId: 'res02', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 3, 16, 10, 0), details: {'employeeId': 'emp20'}),
  AuditLog(id: 'al05', action: 'EMPLOYEE_ADD', entityType: 'Employee',
      entityId: 'emp50', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 3, 11, 9, 0), details: {'name': 'Zaher Samy'}),
  AuditLog(id: 'al06', action: 'ROLE_CREATE', entityType: 'Role',
      entityId: 'r22', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 2, 20, 11, 0), details: {'title': 'Junior Data Analyst'}),
  AuditLog(id: 'al07', action: 'LEAVE_REJECT', entityType: 'LeaveRequest',
      entityId: 'lr07', performedBy: 'Tarek Mansour',
      timestamp: DateTime(2026, 4, 8, 16, 0), details: {'reason': 'Critical sprint'}),
  AuditLog(id: 'al08', action: 'LOGIN', entityType: 'User',
      entityId: 'emp14', performedBy: 'Rana Essam',
      timestamp: DateTime(2026, 4, 12, 8, 5), details: {}),
];
