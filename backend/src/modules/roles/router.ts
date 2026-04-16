// src/modules/roles/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import { auditLog } from '../../middleware/auditLog';
import * as svc from '../skills/service';

const router = Router();

const createSchema = z.object({
  id:          z.string().optional(),
  title:       z.string().min(1),
  department:  z.string().min(1),
  level:       z.enum(['junior', 'mid', 'senior', 'lead', 'manager']),
  description: z.string().optional(),
  requiredSkills: z.array(z.object({
    skillId:        z.string(),
    minProficiency: z.number().int().min(1).max(5),
  })).optional(),
});

// GET /roles
router.get('/', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getAllRoles()); } catch (err) { next(err); }
});

// GET /roles/:id
router.get('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getRoleById(req.params['id']!)); } catch (err) { next(err); }
});

// POST /roles — hr_admin
router.post('/', authenticate, authorize('hr_admin'), validateBody(createSchema),
  auditLog({ action: 'CREATE', entityType: 'job_role' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.status(201).json(await svc.createRole(req.body)); } catch (err) { next(err); }
  },
);

export default router;
