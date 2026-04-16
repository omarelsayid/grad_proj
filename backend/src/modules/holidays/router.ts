// src/modules/holidays/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { holidays } from '../../db/schema';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { AppError } from '../../middleware/errorHandler';

const router = Router();

const createSchema = z.object({
  name:        z.string().min(1),
  date:        z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  type:        z.enum(['public', 'company', 'optional']).default('public'),
  description: z.string().optional(),
});

// GET /holidays
router.get('/', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try {
    res.json(await db.query.holidays.findMany({ orderBy: (t, { asc }) => [asc(t.date)] }));
  } catch (err) { next(err); }
});

// POST /holidays — hr_admin
router.post('/', authenticate, authorize('hr_admin'), validateBody(createSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = crypto.randomUUID();
      await db.insert(holidays).values({ id, ...req.body });
      res.status(201).json(await db.query.holidays.findFirst({ where: eq(holidays.id, id) }));
    } catch (err) { next(err); }
  },
);

// DELETE /holidays/:id — hr_admin
router.delete('/:id', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const h = await db.query.holidays.findFirst({ where: eq(holidays.id, req.params['id']!) });
      if (!h) throw new AppError(404, 'Holiday not found', 'NOT_FOUND');
      await db.delete(holidays).where(eq(holidays.id, req.params['id']!));
      res.status(204).send();
    } catch (err) { next(err); }
  },
);

export default router;
