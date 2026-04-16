// src/modules/resignations/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import * as svc from './service';

const router = Router();

const createSchema = z.object({
  lastWorkingDate:  z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  noticePeriodDays: z.number().int().optional(),
  reason:           z.string().optional(),
});

// GET /resignations
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (req.user!.role === 'employee') {
      return res.json(await svc.getAll(req.user!.employeeId ?? undefined));
    }
    res.json(await svc.getAll(req.query['employeeId'] as string | undefined));
  } catch (err) { next(err); }
});

// POST /resignations
router.post('/', authenticate, authorize('employee'),
  validateBody(createSchema),
  auditLog({ action: 'CREATE', entityType: 'resignation' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
      res.status(201).json(await svc.create(req.user!.employeeId, req.body));
    } catch (err) { next(err); }
  },
);

// PATCH /resignations/:id — hr_admin approves/rejects; employee withdraws
router.patch('/:id', authenticate,
  validateBody(z.object({ status: z.enum(['approved', 'rejected', 'withdrawn']) })),
  auditLog({ action: 'UPDATE', entityType: 'resignation' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { status } = req.body as { status: 'approved' | 'rejected' | 'withdrawn' };
      if (status !== 'withdrawn') authorize('hr_admin')(req, res, () => {});
      res.json(await svc.updateStatus(req.params['id']!, status, req.user!.employeeId ?? undefined));
    } catch (err) { next(err); }
  },
);

export default router;
