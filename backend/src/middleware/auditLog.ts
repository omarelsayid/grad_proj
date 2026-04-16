// src/middleware/auditLog.ts — Automatic audit logging for mutating operations
import { Request, Response, NextFunction } from 'express';
import { db } from '../db';
import { auditLogs } from '../db/schema';
import { logger } from '../config/logger';

interface AuditOptions {
  action:     string;  // CREATE | UPDATE | DELETE | LOGIN | LOGOUT
  entityType: string;  // employee | leave_request | payroll | ...
}

/**
 * Middleware factory that records an audit log entry after a successful response.
 * Usage:  router.post('/', authenticate, auditLog({ action: 'CREATE', entityType: 'employee' }), handler)
 */
export function auditLog({ action, entityType }: AuditOptions) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const originalJson = res.json.bind(res);

    res.json = function (body: unknown) {
      res.json = originalJson;  // restore to avoid recursion
      const result = originalJson(body);

      if (res.statusCode < 400) {
        const entityId =
          (typeof body === 'object' && body !== null && 'id' in body)
            ? String((body as Record<string, unknown>)['id'])
            : req.params['id'];

        db.insert(auditLogs).values({
          userId:     req.user?.sub ?? null,
          action,
          entityType,
          entityId:   entityId ?? null,
          newValues:  action !== 'DELETE' ? (body as Record<string, unknown>) : null,
          ipAddress:  req.ip ?? null,
          userAgent:  req.get('user-agent') ?? null,
        }).catch((err: Error) => logger.error('Audit log insert failed', { error: err.message }));
      }

      return result;
    };

    next();
  };
}
