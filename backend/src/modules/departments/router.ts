// src/modules/departments/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { departments } from '../../db/schema';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import { AppError } from '../../middleware/errorHandler';

const router = Router();

const schema = z.object({
  name:        z.string().min(1),
  description: z.string().optional(),
  managerId:   z.string().optional(),
});

// GET /departments — all users
router.get('/', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try { res.json(await db.query.departments.findMany({ orderBy: (t, { asc }) => [asc(t.name)] })); }
  catch (err) { next(err); }
});

// GET /departments/:id
router.get('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const d = await db.query.departments.findFirst({ where: eq(departments.id, req.params['id']!) });
    if (!d) throw new AppError(404, 'Department not found', 'NOT_FOUND');
    res.json(d);
  } catch (err) { next(err); }
});

// POST /departments — hr_admin
router.post('/', authenticate, authorize('hr_admin'), validateBody(schema),
  auditLog({ action: 'CREATE', entityType: 'department' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const id = crypto.randomUUID();
      await db.insert(departments).values({ id, ...req.body });
      res.status(201).json(await db.query.departments.findFirst({ where: eq(departments.id, id) }));
    } catch (err) { next(err); }
  },
);

// PATCH /departments/:id
router.patch('/:id', authenticate, authorize('hr_admin'), validateBody(schema.partial()),
  auditLog({ action: 'UPDATE', entityType: 'department' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      await db.update(departments).set({ ...req.body, updatedAt: new Date() }).where(eq(departments.id, req.params['id']!));
      res.json(await db.query.departments.findFirst({ where: eq(departments.id, req.params['id']!) }));
    } catch (err) { next(err); }
  },
);

// DELETE /departments/:id
router.delete('/:id', authenticate, authorize('hr_admin'),
  auditLog({ action: 'DELETE', entityType: 'department' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      await db.delete(departments).where(eq(departments.id, req.params['id']!));
      res.status(204).send();
    } catch (err) { next(err); }
  },
);

export default router;
