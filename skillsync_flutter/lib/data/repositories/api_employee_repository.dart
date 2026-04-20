// lib/data/repositories/api_employee_repository.dart
import '../../domain/entities/attendance_record.dart';
import '../../domain/entities/app_notification.dart';
import '../../domain/entities/employee.dart';
import '../../domain/entities/employee_skill.dart';
import '../../domain/entities/leave_balance.dart';
import '../../domain/entities/leave_request.dart';
import '../../domain/entities/payroll_record.dart';
import '../../domain/entities/resignation_request.dart';
import '../../domain/entities/todo.dart';
import '../../domain/repositories/employee_repository.dart';
import '../../services/api_client.dart';

class ApiEmployeeRepository implements EmployeeRepository {
  final ApiClient _api = ApiClient.instance;

  // ── Parsing helpers ──────────────────────────────────────────────────────────

  Employee _parseEmployee(Map<String, dynamic> j) {
    final rawSkills = j['skills'] as List<dynamic>? ?? [];
    return Employee(
      id:                j['id'] as String,
      name:              j['name'] as String,
      email:             j['email'] as String,
      avatarUrl:         j['avatarUrl'] as String? ?? '',
      currentRole:       j['currentRole'] as String,
      roleId:            j['roleId'] as String,
      department:        j['department'] as String,
      joinDate:          DateTime.parse(j['joinDate'] as String),
      salary:            (j['salary'] as num).toDouble(),
      phone:             j['phone'] as String? ?? '',
      commuteDistance:   j['commuteDistance'] as String? ?? 'moderate',
      satisfactionScore: (j['satisfactionScore'] as num? ?? 70).toDouble(),
      skills: rawSkills.map((s) {
        final sk = s as Map<String, dynamic>;
        return EmployeeSkill(
          skillId:      sk['skillId'] as String,
          proficiency:  (sk['proficiency'] as num).toInt(),
          lastAssessed: DateTime.parse(sk['lastAssessed'] as String),
        );
      }).toList(),
    );
  }

  AttendanceRecord _parseAttendance(Map<String, dynamic> j) {
    final dateStr = j['date'] as String;
    DateTime? parseTime(String? t) {
      if (t == null || t.isEmpty) return null;
      // t may be "HH:MM" or full ISO
      if (t.contains('T')) return DateTime.parse(t);
      final parts = t.split(':');
      final d = DateTime.parse(dateStr);
      return DateTime(d.year, d.month, d.day, int.parse(parts[0]), int.parse(parts[1]));
    }

    AttendanceStatus parseStatus(String s) {
      switch (s) {
        case 'late':      return AttendanceStatus.late;
        case 'absent':    return AttendanceStatus.absent;
        case 'half_day':  return AttendanceStatus.halfDay;
        case 'remote':    return AttendanceStatus.remote;
        default:          return AttendanceStatus.present;
      }
    }

    return AttendanceRecord(
      id:         j['id'] as String,
      employeeId: j['employeeId'] as String? ?? j['employee_id'] as String,
      date:       DateTime.parse(dateStr),
      checkIn:    parseTime(j['checkIn'] as String?),
      checkOut:   parseTime(j['checkOut'] as String?),
      status:     parseStatus(j['status'] as String? ?? 'present'),
      type:       j['type'] as String? ?? 'office',
    );
  }

  LeaveRequest _parseLeaveRequest(Map<String, dynamic> j) {
    LeaveStatus parseStatus(String s) {
      switch (s) {
        case 'approved':  return LeaveStatus.approved;
        case 'rejected':  return LeaveStatus.rejected;
        default:          return LeaveStatus.pending;
      }
    }
    return LeaveRequest(
      id:         j['id'] as String,
      employeeId: j['employeeId'] as String? ?? j['employee_id'] as String,
      leaveType:  j['leaveType'] as String? ?? j['leave_type'] as String,
      startDate:  DateTime.parse(j['startDate'] as String? ?? j['start_date'] as String),
      endDate:    DateTime.parse(j['endDate'] as String? ?? j['end_date'] as String),
      reason:     j['reason'] as String? ?? '',
      status:     parseStatus(j['status'] as String? ?? 'pending'),
    );
  }

  PayrollRecord _parsePayroll(Map<String, dynamic> j) {
    PayrollStatus parseStatus(String s) {
      switch (s) {
        case 'processed': return PayrollStatus.processed;
        case 'paid':      return PayrollStatus.paid;
        default:          return PayrollStatus.pending;
      }
    }
    return PayrollRecord(
      id:          j['id'] as String,
      employeeId:  j['employeeId'] as String? ?? j['employee_id'] as String,
      month:       (j['month'] as num).toInt(),
      year:        (j['year'] as num).toInt(),
      basicSalary: (j['basicSalary'] as num? ?? j['basic_salary'] as num).toDouble(),
      allowances:  (j['allowances'] as num? ?? 0).toDouble(),
      deductions:  (j['deductions'] as num? ?? 0).toDouble(),
      status:      parseStatus(j['status'] as String? ?? 'draft'),
    );
  }

  Todo _parseTodo(Map<String, dynamic> j) {
    TodoPriority parsePriority(String p) {
      switch (p) {
        case 'high':
        case 'urgent': return TodoPriority.high;
        case 'low':    return TodoPriority.low;
        default:       return TodoPriority.medium;
      }
    }
    final dueDateRaw = j['dueDate'] as String? ?? j['due_date'] as String?;
    return Todo(
      id:          j['id'] as String,
      employeeId:  j['employeeId'] as String? ?? j['employee_id'] as String,
      title:       j['title'] as String,
      description: j['description'] as String? ?? '',
      dueDate:     dueDateRaw != null ? DateTime.parse(dueDateRaw) : DateTime.now().add(const Duration(days: 7)),
      priority:    parsePriority(j['priority'] as String? ?? 'medium'),
      completed:   j['completed'] as bool? ?? false,
    );
  }

  AppNotification _parseNotification(Map<String, dynamic> j) {
    return AppNotification(
      id:        j['id'] as String,
      userId:    j['employeeId'] as String? ?? j['employee_id'] as String? ?? '',
      title:     j['title'] as String,
      message:   j['message'] as String,
      type:      j['type'] as String? ?? 'info',
      isRead:    j['read'] as bool? ?? false,
      createdAt: DateTime.parse(j['createdAt'] as String? ?? j['created_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  ResignationRequest _parseResignation(Map<String, dynamic> j) {
    ResignationStatus parseStatus(String s) {
      switch (s) {
        case 'approved':  return ResignationStatus.approved;
        case 'rejected':  return ResignationStatus.rejected;
        default:          return ResignationStatus.pending;
      }
    }
    return ResignationRequest(
      id:               j['id'] as String,
      employeeId:       j['employeeId'] as String? ?? j['employee_id'] as String,
      lastWorkingDate:  DateTime.parse(j['lastWorkingDate'] as String? ?? j['last_working_date'] as String),
      noticePeriodDays: (j['noticePeriodDays'] as num? ?? j['notice_period_days'] as num? ?? 30).toInt(),
      reason:           j['reason'] as String? ?? '',
      status:           parseStatus(j['status'] as String? ?? 'pending'),
      submittedAt:      DateTime.parse(j['createdAt'] as String? ?? j['created_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  // ── EmployeeRepository implementation ───────────────────────────────────────

  @override
  Future<List<Employee>> getAll() async {
    final list = await _api.getEmployees();
    return list.map((e) => _parseEmployee(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<Employee?> getById(String id) async {
    try {
      final data = await _api.getEmployeeById(id);
      return _parseEmployee(data);
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
  }

  @override
  Future<Employee> add(Employee employee) async {
    final data = await _api.getEmployeeById(employee.id);
    return _parseEmployee(data);
  }

  @override
  Future<Employee> update(Employee employee) async {
    final data = await _api.getEmployeeById(employee.id);
    return _parseEmployee(data);
  }

  // ── Attendance ───────────────────────────────────────────────────────────────

  @override
  Future<List<AttendanceRecord>> getAttendance(String employeeId) async {
    final list = await _api.getAttendance();
    return list
        .map((e) => _parseAttendance(e as Map<String, dynamic>))
        .where((a) => a.employeeId == employeeId)
        .toList();
  }

  // ── Leaves ───────────────────────────────────────────────────────────────────

  @override
  Future<LeaveBalance> getLeaveBalance(String employeeId) async {
    final rows = await _api.getLeaveBalances();
    int annualTotal = 21, annualUsed = 0;
    int sickTotal = 10, sickUsed = 0;
    int compassionateTotal = 5, compassionateUsed = 0;

    for (final r in rows) {
      final row = r as Map<String, dynamic>;
      final type = row['leaveType'] as String? ?? row['leave_type'] as String? ?? '';
      final total = (row['totalDays'] as num? ?? row['total_days'] as num? ?? 0).toInt();
      final used  = (row['usedDays'] as num? ?? row['used_days'] as num? ?? 0).toInt();
      switch (type) {
        case 'annual':        annualTotal = total; annualUsed = used;
        case 'sick':          sickTotal = total;   sickUsed = used;
        case 'compassionate': compassionateTotal = total; compassionateUsed = used;
      }
    }

    return LeaveBalance(
      employeeId:         employeeId,
      annualTotal:        annualTotal,
      annualUsed:         annualUsed,
      sickTotal:          sickTotal,
      sickUsed:           sickUsed,
      compassionateTotal: compassionateTotal,
      compassionateUsed:  compassionateUsed,
    );
  }

  @override
  Future<List<LeaveRequest>> getLeaveRequests({String? employeeId}) async {
    final list = await _api.getLeaves();
    final parsed = list.map((e) => _parseLeaveRequest(e as Map<String, dynamic>)).toList();
    if (employeeId != null) return parsed.where((r) => r.employeeId == employeeId).toList();
    return parsed;
  }

  @override
  Future<LeaveRequest> submitLeaveRequest(LeaveRequest request) async {
    final data = await _api.createLeaveRequest({
      'leaveType': request.leaveType,
      'startDate': request.startDate.toIso8601String().split('T').first,
      'endDate':   request.endDate.toIso8601String().split('T').first,
      'reason':    request.reason,
    });
    return _parseLeaveRequest(data);
  }

  @override
  Future<LeaveRequest> updateLeaveStatus(String id, LeaveStatus status) async {
    final data = status == LeaveStatus.approved
        ? await _api.approveLeave(id)
        : await _api.rejectLeave(id);
    return _parseLeaveRequest(data);
  }

  // ── Payroll ──────────────────────────────────────────────────────────────────

  @override
  Future<List<PayrollRecord>> getPayroll({String? employeeId, int? month, int? year}) async {
    final list = await _api.getPayroll(month: month, year: year);
    final parsed = list.map((e) => _parsePayroll(e as Map<String, dynamic>)).toList();
    if (employeeId != null) return parsed.where((p) => p.employeeId == employeeId).toList();
    return parsed;
  }

  // ── Todos ────────────────────────────────────────────────────────────────────

  @override
  Future<List<Todo>> getTodos(String employeeId) async {
    final list = await _api.getTodos();
    return list.map((e) => _parseTodo(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<Todo> addTodo(Todo todo) async {
    final data = await _api.createTodo({
      'title':       todo.title,
      'description': todo.description,
      'dueDate':     todo.dueDate.toIso8601String().split('T').first,
      'priority':    todo.priority.name,
    });
    return _parseTodo(data);
  }

  @override
  Future<Todo> updateTodo(Todo todo) async {
    final data = await _api.updateTodo(todo.id, {
      'title':       todo.title,
      'description': todo.description,
      'dueDate':     todo.dueDate.toIso8601String().split('T').first,
      'priority':    todo.priority.name,
      'completed':   todo.completed,
    });
    return _parseTodo(data);
  }

  @override
  Future<void> deleteTodo(String id) => _api.deleteTodo(id);

  // ── Notifications ────────────────────────────────────────────────────────────

  @override
  Future<List<AppNotification>> getNotifications(String userId) async {
    final list = await _api.getNotifications();
    return list.map((e) => _parseNotification(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<AppNotification> markNotificationRead(String id) async {
    await _api.markNotificationRead(id);
    // Return a placeholder — screens refresh after marking read
    return AppNotification(
      id: id, userId: '', title: '', message: '',
      type: 'info', isRead: true, createdAt: DateTime.now(),
    );
  }

  // ── Resignations ─────────────────────────────────────────────────────────────

  @override
  Future<List<ResignationRequest>> getResignations({String? employeeId}) async {
    final list = await _api.getResignations();
    final parsed = list.map((e) => _parseResignation(e as Map<String, dynamic>)).toList();
    if (employeeId != null) return parsed.where((r) => r.employeeId == employeeId).toList();
    return parsed;
  }

  @override
  Future<ResignationRequest> submitResignation(ResignationRequest request) async {
    final data = await _api.submitResignation({
      'lastWorkingDate':  request.lastWorkingDate.toIso8601String().split('T').first,
      'noticePeriodDays': request.noticePeriodDays,
      'reason':           request.reason,
    });
    return _parseResignation(data);
  }

  @override
  Future<ResignationRequest> updateResignationStatus(String id, ResignationStatus status) async {
    // Backend doesn't have a dedicated resign status endpoint — return current data
    final list = await _api.getResignations();
    final match = list.firstWhere(
      (e) => (e as Map<String, dynamic>)['id'] == id,
      orElse: () => <String, dynamic>{'id': id, 'employeeId': '', 'lastWorkingDate': DateTime.now().toIso8601String(), 'status': status.name},
    );
    return _parseResignation(match as Map<String, dynamic>);
  }
}
