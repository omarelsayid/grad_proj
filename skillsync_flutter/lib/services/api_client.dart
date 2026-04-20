// lib/services/api_client.dart
// HTTP client that wraps all backend API calls.
// Replace mock data calls with these methods throughout the app.
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final int statusCode;
  final String message;
  final String? code;

  const ApiException(this.statusCode, this.message, {this.code});

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  static const _baseUrl = 'http://localhost:3000/api/v1';

  String? _accessToken;
  String? _refreshToken;

  ApiClient._();
  static final ApiClient instance = ApiClient._();

  void setTokens({required String accessToken, required String refreshToken}) {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
  }

  void clearTokens() {
    _accessToken = null;
    _refreshToken = null;
  }

  bool get isAuthenticated => _accessToken != null;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  // ── Internal request helper ─────────────────────────────────────────────────
  Future<dynamic> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool retry = true,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');

    http.Response response;
    switch (method) {
      case 'GET':
        response = await http.get(uri, headers: _headers);
      case 'POST':
        response = await http.post(uri, headers: _headers, body: body != null ? jsonEncode(body) : null);
      case 'PUT':
        response = await http.put(uri, headers: _headers, body: body != null ? jsonEncode(body) : null);
      case 'PATCH':
        response = await http.patch(uri, headers: _headers, body: body != null ? jsonEncode(body) : null);
      case 'DELETE':
        response = await http.delete(uri, headers: _headers);
      default:
        throw ApiException(0, 'Unknown HTTP method: $method');
    }

    // Auto-refresh on 401
    if (response.statusCode == 401 && retry && _refreshToken != null) {
      final refreshed = await _tryRefresh();
      if (refreshed) return _request(method, path, body: body, retry: false);
    }

    return _handleResponse(response);
  }

  Future<bool> _tryRefresh() async {
    if (_refreshToken == null) return false;
    try {
      final res = await http.post(
        Uri.parse('$_baseUrl/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refreshToken': _refreshToken}),
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        _accessToken  = data['accessToken'] as String?;
        _refreshToken = data['refreshToken'] as String? ?? _refreshToken;
        return true;
      }
    } catch (_) {}
    clearTokens();
    return false;
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode == 204) return null;

    final body = response.body.isEmpty ? null : jsonDecode(response.body);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    final errMsg  = (body is Map ? body['error'] as String? : null) ?? response.reasonPhrase ?? 'Unknown error';
    final errCode = (body is Map ? body['code'] as String? : null);
    throw ApiException(response.statusCode, errMsg, code: errCode);
  }

  // ── Auth ─────────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _request('POST', '/auth/login', body: {'email': email, 'password': password}) as Map<String, dynamic>;
    setTokens(
      accessToken:  data['accessToken'] as String,
      refreshToken: data['refreshToken'] as String,
    );
    return data;
  }

  Future<Map<String, dynamic>> register(String email, String password, String name, String role) async {
    final data = await _request('POST', '/auth/register',
      body: {'email': email, 'password': password, 'name': name, 'role': role},
    ) as Map<String, dynamic>;
    setTokens(
      accessToken:  data['accessToken'] as String,
      refreshToken: data['refreshToken'] as String,
    );
    return data;
  }

  Future<void> logout() async {
    if (_refreshToken == null) return;
    await _request('POST', '/auth/logout', body: {'refreshToken': _refreshToken});
    clearTokens();
  }

  // ── Employees ─────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getEmployees({String? department, String? search}) async {
    final q = {if (department != null) 'department': department, if (search != null) 'search': search};
    final path = q.isNotEmpty ? '/employees?${_encodeQuery(q)}' : '/employees';
    return (await _request('GET', path)) as List<dynamic>;
  }

  Future<Map<String, dynamic>> getEmployeeById(String id) async =>
      (await _request('GET', '/employees/$id')) as Map<String, dynamic>;

  Future<Map<String, dynamic>> getMyProfile() async =>
      (await _request('GET', '/employees/me')) as Map<String, dynamic>;

  Future<Map<String, dynamic>> updateEmployeeSkill(
    String employeeId, String skillId, int proficiency, String lastAssessed,
  ) async =>
      (await _request('PUT', '/employees/$employeeId/skills/$skillId',
        body: {'skillId': skillId, 'proficiency': proficiency, 'lastAssessed': lastAssessed},
      )) as Map<String, dynamic>;

  // ── Skills & Roles ────────────────────────────────────────────────────────────
  Future<List<dynamic>> getSkills() async =>
      (await _request('GET', '/skills')) as List<dynamic>;

  Future<List<dynamic>> getSkillChains() async =>
      (await _request('GET', '/skills/chains')) as List<dynamic>;

  Future<List<dynamic>> getRoles() async =>
      (await _request('GET', '/roles')) as List<dynamic>;

  Future<Map<String, dynamic>> getRoleById(String id) async =>
      (await _request('GET', '/roles/$id')) as Map<String, dynamic>;

  // ── Attendance ────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getAttendance({String? from, String? to}) async {
    final q = {if (from != null) 'from': from, if (to != null) 'to': to};
    final path = q.isNotEmpty ? '/attendance?${_encodeQuery(q)}' : '/attendance';
    return (await _request('GET', path)) as List<dynamic>;
  }

  Future<dynamic> checkIn()  async => _request('POST', '/attendance/check-in');
  Future<dynamic> checkOut() async => _request('POST', '/attendance/check-out');

  // ── Leaves ────────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getLeaves({String? status}) async {
    final path = status != null ? '/leaves?status=$status' : '/leaves';
    return (await _request('GET', path)) as List<dynamic>;
  }

  Future<List<dynamic>> getLeaveBalances() async =>
      (await _request('GET', '/leaves/balances')) as List<dynamic>;

  Future<Map<String, dynamic>> createLeaveRequest(Map<String, dynamic> data) async =>
      (await _request('POST', '/leaves', body: data)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> approveLeave(String id) async =>
      (await _request('PATCH', '/leaves/$id/approve')) as Map<String, dynamic>;

  Future<Map<String, dynamic>> rejectLeave(String id) async =>
      (await _request('PATCH', '/leaves/$id/reject')) as Map<String, dynamic>;

  // ── Payroll ───────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getPayroll({int? month, int? year}) async {
    final q = {if (month != null) 'month': '$month', if (year != null) 'year': '$year'};
    final path = q.isNotEmpty ? '/payroll?${_encodeQuery(q)}' : '/payroll';
    return (await _request('GET', path)) as List<dynamic>;
  }

  // ── Todos ─────────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getTodos() async =>
      (await _request('GET', '/todos')) as List<dynamic>;

  Future<Map<String, dynamic>> createTodo(Map<String, dynamic> data) async =>
      (await _request('POST', '/todos', body: data)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> updateTodo(String id, Map<String, dynamic> data) async =>
      (await _request('PATCH', '/todos/$id', body: data)) as Map<String, dynamic>;

  Future<void> deleteTodo(String id) async =>
      _request('DELETE', '/todos/$id');

  // ── Notifications ─────────────────────────────────────────────────────────────
  Future<List<dynamic>> getNotifications() async =>
      (await _request('GET', '/notifications')) as List<dynamic>;

  Future<void> markNotificationRead(String id) async =>
      _request('PATCH', '/notifications/$id/read');

  Future<void> deleteNotification(String id) async =>
      _request('DELETE', '/notifications/$id');

  // ── Chat ──────────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getChatHistory({int limit = 50}) async =>
      (await _request('GET', '/chat/history?limit=$limit')) as List<dynamic>;

  Future<String> askAI(String question) async {
    final data = await _request('POST', '/chat/ask', body: {'question': question}) as Map<String, dynamic>;
    return data['answer'] as String? ?? '';
  }

  // ── Resignations ──────────────────────────────────────────────────────────────
  Future<List<dynamic>> getResignations() async =>
      (await _request('GET', '/resignations')) as List<dynamic>;

  Future<Map<String, dynamic>> submitResignation(Map<String, dynamic> data) async =>
      (await _request('POST', '/resignations', body: data)) as Map<String, dynamic>;

  // ── Holidays ──────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getHolidays() async =>
      (await _request('GET', '/holidays')) as List<dynamic>;

  // ── Departments ───────────────────────────────────────────────────────────────
  Future<List<dynamic>> getDepartments() async =>
      (await _request('GET', '/departments')) as List<dynamic>;

  // ── ML / Scoring ─────────────────────────────────────────────────────────────
  Future<List<dynamic>> getOrgSkillGaps() async =>
      (await _request('GET', '/ml/org-skill-gaps')) as List<dynamic>;

  Future<List<dynamic>> getReplacementCandidates(String departingId, String roleId, {int limit = 5}) async {
    final data = await _request('POST', '/ml/replacements',
      body: {'departingEmployeeId': departingId, 'roleId': roleId, 'limit': limit},
    );
    return data as List<dynamic>;
  }

  Future<Map<String, dynamic>> getTurnoverPredictions(Map<String, dynamic> payload) async =>
      (await _request('POST', '/ml/turnover', body: payload)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> getMlTurnoverRisk(Map<String, dynamic> payload) async =>
      (await _request('POST', '/ml/turnover', body: payload)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> getMlRoleFit(Map<String, dynamic> payload) async =>
      (await _request('POST', '/ml/role-fit', body: payload)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> getMlSkillGaps() async =>
      (await _request('GET', '/ml/skill-gaps')) as Map<String, dynamic>;

  Future<Map<String, dynamic>> getMlLearningPath(Map<String, dynamic> payload) async =>
      (await _request('POST', '/ml/learning-path', body: payload)) as Map<String, dynamic>;

  // ── Roles mutations ───────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> createRole(Map<String, dynamic> data) async =>
      (await _request('POST', '/roles', body: data)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> updateRole(String id, Map<String, dynamic> data) async =>
      (await _request('PATCH', '/roles/$id', body: data)) as Map<String, dynamic>;

  Future<void> deleteRole(String id) async => _request('DELETE', '/roles/$id');

  // ── Skills mutations ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> createSkill(Map<String, dynamic> data) async =>
      (await _request('POST', '/skills', body: data)) as Map<String, dynamic>;

  Future<Map<String, dynamic>> updateSkill(String id, Map<String, dynamic> data) async =>
      (await _request('PATCH', '/skills/$id', body: data)) as Map<String, dynamic>;

  Future<void> deleteSkill(String id) async => _request('DELETE', '/skills/$id');

  // ── Audit ─────────────────────────────────────────────────────────────────────
  Future<List<dynamic>> getAuditLog({String? entityType}) async {
    final path = entityType != null ? '/audit?entityType=$entityType' : '/audit';
    return (await _request('GET', path)) as List<dynamic>;
  }

  // ── Utility ───────────────────────────────────────────────────────────────────
  String _encodeQuery(Map<String, String> params) =>
      params.entries.map((e) => '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}').join('&');
}
