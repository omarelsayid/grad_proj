// lib/data/repositories/mock_employee_repository.dart
import '../../domain/entities/employee.dart';
import '../../domain/entities/attendance_record.dart';
import '../../domain/entities/leave_balance.dart';
import '../../domain/entities/leave_request.dart';
import '../../domain/entities/payroll_record.dart';
import '../../domain/entities/todo.dart';
import '../../domain/entities/app_notification.dart';
import '../../domain/entities/resignation_request.dart';
import '../../domain/repositories/employee_repository.dart';
import '../mock/mock_employees.dart';
import '../mock/mock_attendance.dart';
import '../mock/mock_static_data.dart' as _s;

class MockEmployeeRepository implements EmployeeRepository {
  final List<Employee> _employees = List.from(mockEmployees);
  final Map<String, List<Todo>> _todos = {};
  final Map<String, List<AppNotification>> _notifications = {};
  final List<LeaveRequest> _leaves = List.from(_s.mockLeaveRequests);
  final List<ResignationRequest> _resignations = List.from(_s.mockResignations);

  @override
  Future<List<Employee>> getAll() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return List.unmodifiable(_employees);
  }

  @override
  Future<Employee?> getById(String id) async {
    await Future.delayed(const Duration(milliseconds: 100));
    try {
      return _employees.firstWhere((e) => e.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<Employee> add(Employee employee) async {
    await Future.delayed(const Duration(milliseconds: 200));
    _employees.add(employee);
    return employee;
  }

  @override
  Future<Employee> update(Employee employee) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _employees.indexWhere((e) => e.id == employee.id);
    if (idx != -1) _employees[idx] = employee;
    return employee;
  }

  @override
  Future<List<AttendanceRecord>> getAttendance(String employeeId) async {
    await Future.delayed(const Duration(milliseconds: 200));
    return generateAttendance(employeeId);
  }

  @override
  Future<LeaveBalance> getLeaveBalance(String employeeId) async {
    await Future.delayed(const Duration(milliseconds: 100));
    return _s.getLeaveBalance(employeeId);
  }

  @override
  Future<List<LeaveRequest>> getLeaveRequests({String? employeeId}) async {
    await Future.delayed(const Duration(milliseconds: 200));
    if (employeeId != null) {
      return _leaves.where((l) => l.employeeId == employeeId).toList();
    }
    return List.unmodifiable(_leaves);
  }

  @override
  Future<LeaveRequest> submitLeaveRequest(LeaveRequest request) async {
    await Future.delayed(const Duration(milliseconds: 300));
    _leaves.add(request);
    return request;
  }

  @override
  Future<LeaveRequest> updateLeaveStatus(String id, LeaveStatus status) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _leaves.indexWhere((l) => l.id == id);
    if (idx != -1) {
      _leaves[idx] = _leaves[idx].copyWith(status: status);
      return _leaves[idx];
    }
    throw Exception('Leave request not found: $id');
  }

  @override
  Future<List<PayrollRecord>> getPayroll({String? employeeId, int? month, int? year}) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final emp = employeeId != null
        ? _employees.where((e) => e.id == employeeId).toList()
        : _employees;
    final records = <PayrollRecord>[];
    for (final e in emp) {
      records.addAll(_s.getPayrollForEmployee(e.id, e.salary));
    }
    var result = records;
    if (month != null) result = result.where((p) => p.month == month).toList();
    if (year != null) result = result.where((p) => p.year == year).toList();
    return result;
  }

  @override
  Future<List<Todo>> getTodos(String employeeId) async {
    await Future.delayed(const Duration(milliseconds: 100));
    _todos[employeeId] ??= _s.getInitialTodos(employeeId);
    return List.unmodifiable(_todos[employeeId]!);
  }

  @override
  Future<Todo> addTodo(Todo todo) async {
    _todos[todo.employeeId] ??= [];
    _todos[todo.employeeId]!.add(todo);
    return todo;
  }

  @override
  Future<Todo> updateTodo(Todo todo) async {
    final list = _todos[todo.employeeId];
    if (list != null) {
      final idx = list.indexWhere((t) => t.id == todo.id);
      if (idx != -1) list[idx] = todo;
    }
    return todo;
  }

  @override
  Future<void> deleteTodo(String id) async {
    for (final list in _todos.values) {
      list.removeWhere((t) => t.id == id);
    }
  }

  @override
  Future<List<AppNotification>> getNotifications(String userId) async {
    await Future.delayed(const Duration(milliseconds: 100));
    _notifications[userId] ??= _s.getNotificationsForUser(userId);
    return List.unmodifiable(_notifications[userId]!);
  }

  @override
  Future<AppNotification> markNotificationRead(String id) async {
    for (final list in _notifications.values) {
      final idx = list.indexWhere((n) => n.id == id);
      if (idx != -1) {
        list[idx] = list[idx].copyWith(isRead: true);
        return list[idx];
      }
    }
    throw Exception('Notification not found: $id');
  }

  @override
  Future<List<ResignationRequest>> getResignations({String? employeeId}) async {
    await Future.delayed(const Duration(milliseconds: 200));
    if (employeeId != null) {
      return _resignations.where((r) => r.employeeId == employeeId).toList();
    }
    return List.unmodifiable(_resignations);
  }

  @override
  Future<ResignationRequest> submitResignation(ResignationRequest request) async {
    await Future.delayed(const Duration(milliseconds: 300));
    _resignations.add(request);
    return request;
  }

  @override
  Future<ResignationRequest> updateResignationStatus(
      String id, ResignationStatus status) async {
    await Future.delayed(const Duration(milliseconds: 200));
    final idx = _resignations.indexWhere((r) => r.id == id);
    if (idx != -1) {
      _resignations[idx] = _resignations[idx].copyWith(status: status);
      return _resignations[idx];
    }
    throw Exception('Resignation request not found: $id');
  }
}
