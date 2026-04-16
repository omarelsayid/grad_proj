// src/modules/employees/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import * as svc from './service';

const router = Router();

const createSchema = z.object({
  name:              z.string().min(2),
  email:             z.string().email(),
  currentRole:       z.string().min(1),
  roleId:            z.string().min(1),
  department:        z.string().min(1),
  joinDate:          z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  salary:            z.number().positive(),
  phone:             z.string().optional(),
  commuteDistance:   z.enum(['near', 'moderate', 'far', 'very_far']).optional(),
  satisfactionScore: z.number().min(0).max(100).optional(),
});

const updateSchema = createSchema.partial().omit({ email: true });

const skillSchema = z.object({
  skillId:      z.string(),
  proficiency:  z.number().int().min(1).max(5),
  lastAssessed: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

// GET /employees          — manager + hr_admin see all; employee sees own record only
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (req.user!.role === 'employee') {
      const emp = await svc.getByUserId(req.user!.sub);
      return res.json(emp ? [emp] : []);
    }
    const data = await svc.getAll(
      req.query['department'] as string | undefined,
      req.query['search'] as string | undefined,
    );
    res.json(data);
  } catch (err) { next(err); }
});

// GET /employees/me       — current employee profile
router.get('/me', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const emp = await svc.getByUserId(req.user!.sub);
    res.json(emp);
  } catch (err) { next(err); }
});

// GET /employees/:id
router.get('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    // Employees can only see their own record
    if (req.user!.role === 'employee' && req.user!.employeeId !== req.params['id']) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    res.json(await svc.getById(req.params['id']!));
  } catch (err) { next(err); }
});

// POST /employees         — hr_admin only
router.post('/',
  authenticate, authorize('hr_admin'),
  validateBody(createSchema),
  auditLog({ action: 'CREATE', entityType: 'employee' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const emp = await svc.create(req.body);
      res.status(201).json(emp);
    } catch (err) { next(err); }
  },
);

// PATCH /employees/:id    — hr_admin only
router.patch('/:id',
  authenticate, authorize('hr_admin'),
  validateBody(updateSchema),
  auditLog({ action: 'UPDATE', entityType: 'employee' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      res.json(await svc.update(req.params['id']!, req.body));
    } catch (err) { next(err); }
  },
);

// DELETE /employees/:id   — hr_admin only
router.delete('/:id',
  authenticate, authorize('hr_admin'),
  auditLog({ action: 'DELETE', entityType: 'employee' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      await svc.remove(req.params['id']!);
      res.status(204).send();
    } catch (err) { next(err); }
  },
);

// PUT /employees/:id/skills/:skillId  — employee updates own; hr_admin updates any
router.put('/:id/skills/:skillId',
  authenticate,
  validateBody(skillSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (req.user!.role === 'employee' && req.user!.employeeId !== req.params['id']) {
        return res.status(403).json({ error: 'Forbidden' });
      }
      res.json(await svc.upsertSkill(
        req.params['id']!,
        req.params['skillId']!,
        req.body.proficiency,
        req.body.lastAssessed,
      ));
    } catch (err) { next(err); }
  },
);

export default router;
