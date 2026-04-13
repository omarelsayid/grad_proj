// lib/domain/repositories/employee_repository.dart
import '../entities/employee.dart';
import '../entities/attendance_record.dart';
import '../entities/leave_balance.dart';
import '../entities/leave_request.dart';
import '../entities/payroll_record.dart';
import '../entities/todo.dart';
import '../entities/app_notification.dart';
import '../entities/resignation_request.dart';

abstract class EmployeeRepository {
  Future<List<Employee>> getAll();
  Future<Employee?> getById(String id);
  Future<Employee> add(Employee employee);
  Future<Employee> update(Employee employee);

  Future<List<AttendanceRecord>> getAttendance(String employeeId);
  Future<LeaveBalance> getLeaveBalance(String employeeId);
  Future<List<LeaveRequest>> getLeaveRequests({String? employeeId});
  Future<LeaveRequest> submitLeaveRequest(LeaveRequest request);
  Future<LeaveRequest> updateLeaveStatus(String id, LeaveStatus status);

  Future<List<PayrollRecord>> getPayroll({String? employeeId, int? month, int? year});

  Future<List<Todo>> getTodos(String employeeId);
  Future<Todo> addTodo(Todo todo);
  Future<Todo> updateTodo(Todo todo);
  Future<void> deleteTodo(String id);

  Future<List<AppNotification>> getNotifications(String userId);
  Future<AppNotification> markNotificationRead(String id);

  Future<List<ResignationRequest>> getResignations({String? employeeId});
  Future<ResignationRequest> submitResignation(ResignationRequest request);
  Future<ResignationRequest> updateResignationStatus(
      String id, ResignationStatus status);
}
