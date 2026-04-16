// src/modules/leaves/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import * as svc from './service';

const router = Router();

const createSchema = z.object({
  leaveType: z.enum(['annual', 'sick', 'compassionate', 'unpaid', 'maternity', 'paternity']),
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  endDate:   z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  reason:    z.string().optional().default(''),
});

// GET /leaves — employees see own; managers/hr see all
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const status = req.query['status'] as string | undefined;
    if (req.user!.role === 'employee') {
      return res.json(await svc.getAll(req.user!.employeeId ?? undefined, status));
    }
    res.json(await svc.getAll(req.query['employeeId'] as string | undefined, status));
  } catch (err) { next(err); }
});

// GET /leaves/balances — own balances
router.get('/balances', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.json([]);
    const year = req.query['year'] ? parseInt(req.query['year'] as string, 10) : undefined;
    res.json(await svc.getBalances(req.user!.employeeId, year));
  } catch (err) { next(err); }
});

// POST /leaves — create request (employee)
router.post('/', authenticate, authorize('employee'),
  validateBody(createSchema),
  auditLog({ action: 'CREATE', entityType: 'leave_request' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile linked' });
      res.status(201).json(await svc.create(req.user!.employeeId, req.body));
    } catch (err) { next(err); }
  },
);

// PATCH /leaves/:id/approve — manager / hr_admin
router.patch('/:id/approve', authenticate, authorize('manager', 'hr_admin'),
  auditLog({ action: 'UPDATE', entityType: 'leave_request' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      res.json(await svc.approve(req.params['id']!, req.user!.employeeId ?? '', true));
    } catch (err) { next(err); }
  },
);

// PATCH /leaves/:id/reject — manager / hr_admin
router.patch('/:id/reject', authenticate, authorize('manager', 'hr_admin'),
  auditLog({ action: 'UPDATE', entityType: 'leave_request' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      res.json(await svc.approve(req.params['id']!, req.user!.employeeId ?? '', false));
    } catch (err) { next(err); }
  },
);

export default router;
