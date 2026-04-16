// src/middleware/authorize.ts — Role-based access guard
import { Request, Response, NextFunction } from 'express';
import { AppError } from './errorHandler';

type Role = 'employee' | 'manager' | 'hr_admin';

/**
 * Middleware factory that enforces role-based access.
 * Usage:  router.get('/sensitive', authenticate, authorize('hr_admin', 'manager'), handler)
 */
export function authorize(...roles: Role[]) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    if (!req.user) {
      return next(new AppError(401, 'Not authenticated', 'UNAUTHORIZED'));
    }
    if (!roles.includes(req.user.role)) {
      return next(new AppError(403, 'Insufficient permissions', 'FORBIDDEN'));
    }
    next();
  };
}
