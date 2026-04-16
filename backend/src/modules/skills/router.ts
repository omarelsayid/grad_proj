// src/modules/skills/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { validateBody } from '../../middleware/validateBody';
import * as svc from './service';

const router = Router();

// GET /skills
router.get('/', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getAllSkills()); } catch (err) { next(err); }
});

// GET /skills/chains
router.get('/chains', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getAllSkillChains()); } catch (err) { next(err); }
});

// GET /skills/:id
router.get('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getSkillById(req.params['id']!)); } catch (err) { next(err); }
});

// GET /roles
router.get('/roles/all', authenticate, async (_req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getAllRoles()); } catch (err) { next(err); }
});

// GET /roles/:id
router.get('/roles/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try { res.json(await svc.getRoleById(req.params['id']!)); } catch (err) { next(err); }
});

// POST /skills  — hr_admin
const skillSchema = z.object({
  id:          z.string().optional(),
  name:        z.string().min(2),
  category:    z.enum(['technical', 'management', 'soft', 'domain']),
  description: z.string().optional(),
});

router.post('/', authenticate, authorize('hr_admin'), validateBody(skillSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.status(201).json(await svc.createSkill(req.body)); } catch (err) { next(err); }
  },
);

export default router;
