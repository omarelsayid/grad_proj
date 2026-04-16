// src/modules/todos/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { validateBody } from '../../middleware/validateBody';
import * as svc from './service';

const router = Router();

const createSchema = z.object({
  title:       z.string().min(1),
  description: z.string().optional(),
  dueDate:     z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  priority:    z.enum(['low', 'medium', 'high', 'urgent']).optional(),
});

const updateSchema = createSchema.partial().extend({ completed: z.boolean().optional() });

router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.json([]);
    res.json(await svc.getAll(req.user!.employeeId));
  } catch (err) { next(err); }
});

router.post('/', authenticate, validateBody(createSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
      res.status(201).json(await svc.create(req.user!.employeeId, req.body));
    } catch (err) { next(err); }
  },
);

router.patch('/:id', authenticate, validateBody(updateSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
      res.json(await svc.update(req.params['id']!, req.user!.employeeId, req.body));
    } catch (err) { next(err); }
  },
);

router.delete('/:id', authenticate,
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
      await svc.remove(req.params['id']!, req.user!.employeeId);
      res.status(204).send();
    } catch (err) { next(err); }
  },
);

export default router;
