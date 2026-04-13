// lib/domain/entities/audit_log.dart

class AuditLog {
  final String id;
  final String action;
  final String entityType;
  final String entityId;
  final String performedBy;
  final DateTime timestamp;
  final Map<String, dynamic> details;

  const AuditLog({
    required this.id,
    required this.action,
    required this.entityType,
    required this.entityId,
    required this.performedBy,
    required this.timestamp,
    required this.details,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is AuditLog && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
