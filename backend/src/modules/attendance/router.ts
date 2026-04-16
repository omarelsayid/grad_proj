// src/modules/attendance/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import * as svc from './service';

const router = Router();

// GET /attendance — scoped by role
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { from, to, department } = req.query as Record<string, string | undefined>;

    if (req.user!.role === 'employee') {
      if (!req.user!.employeeId) return res.json([]);
      return res.json(await svc.getForEmployee(req.user!.employeeId, from, to));
    }
    res.json(await svc.getAll(from, to, department));
  } catch (err) { next(err); }
});

// GET /attendance/:employeeId — manager / hr_admin
router.get('/:employeeId', authenticate, authorize('manager', 'hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { from, to } = req.query as Record<string, string | undefined>;
      res.json(await svc.getForEmployee(req.params['employeeId']!, from, to));
    } catch (err) { next(err); }
  },
);

// POST /attendance/check-in
router.post('/check-in', authenticate, authorize('employee'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile linked' });
      res.status(201).json(await svc.checkIn(req.user!.employeeId));
    } catch (err) { next(err); }
  },
);

// POST /attendance/check-out
router.post('/check-out', authenticate, authorize('employee'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile linked' });
      res.json(await svc.checkOut(req.user!.employeeId));
    } catch (err) { next(err); }
  },
);

export default router;
