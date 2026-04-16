// src/modules/notifications/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import * as svc from './service';

const router = Router();

// GET /notifications — own inbox
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.json([]);
    res.json(await svc.getAll(req.user!.employeeId));
  } catch (err) { next(err); }
});

// PATCH /notifications/:id/read
router.patch('/:id/read', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
    res.json(await svc.markRead(req.params['id']!, req.user!.employeeId));
  } catch (err) { next(err); }
});

// DELETE /notifications/:id
router.delete('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
    await svc.remove(req.params['id']!, req.user!.employeeId);
    res.status(204).send();
  } catch (err) { next(err); }
});

// POST /notifications/broadcast — hr_admin only
router.post('/broadcast', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      await svc.broadcast(req.body);
      res.status(201).json({ ok: true });
    } catch (err) { next(err); }
  },
);

export default router;
