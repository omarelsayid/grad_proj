// src/modules/payroll/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import * as svc from './service';

const router = Router();

// GET /payroll — employee sees own; others see all/filtered
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { month, year } = req.query as Record<string, string>;
    const m = month ? parseInt(month, 10) : undefined;
    const y = year  ? parseInt(year, 10)  : undefined;

    if (req.user!.role === 'employee') {
      return res.json(await svc.getAll(req.user!.employeeId ?? undefined, m, y));
    }
    res.json(await svc.getAll(req.query['employeeId'] as string | undefined, m, y));
  } catch (err) { next(err); }
});

const createSchema = z.object({
  employeeId:  z.string(),
  month:       z.number().int().min(1).max(12),
  year:        z.number().int().min(2020),
  basicSalary: z.number().positive(),
  allowances:  z.number().min(0).optional(),
  deductions:  z.number().min(0).optional(),
});

const updateSchema = z.object({
  allowances: z.number().min(0).optional(),
  deductions: z.number().min(0).optional(),
  status:     z.enum(['draft', 'processed', 'paid']).optional(),
  paidDate:   z.string().optional(),
});

// POST /payroll — hr_admin
router.post('/', authenticate, authorize('hr_admin'),
  validateBody(createSchema),
  auditLog({ action: 'CREATE', entityType: 'payroll' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.status(201).json(await svc.create(req.body)); } catch (err) { next(err); }
  },
);

// PATCH /payroll/:id — hr_admin
router.patch('/:id', authenticate, authorize('hr_admin'),
  validateBody(updateSchema),
  auditLog({ action: 'UPDATE', entityType: 'payroll' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.json(await svc.update(req.params['id']!, req.body)); } catch (err) { next(err); }
  },
);

// POST /payroll/generate — hr_admin triggers monthly generation
router.post('/generate', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { month, year } = req.body as { month: number; year: number };
      res.json(await svc.generateMonthly(month, year));
    } catch (err) { next(err); }
  },
);

export default router;
