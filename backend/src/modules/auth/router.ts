// src/modules/auth/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { validateBody } from '../../middleware/validateBody';
import { authenticate } from '../../middleware/auth';
import { auditLog } from '../../middleware/auditLog';
import * as svc from './service';

const router = Router();

const registerSchema = z.object({
  email:    z.string().email(),
  password: z.string().min(8),
  name:     z.string().min(2),
  role:     z.enum(['employee', 'manager', 'hr_admin']).default('employee'),
});

const loginSchema = z.object({
  email:    z.string().email(),
  password: z.string().min(1),
});

const refreshSchema = z.object({ refreshToken: z.string().min(1) });

// POST /auth/register
router.post(
  '/register',
  validateBody(registerSchema),
  auditLog({ action: 'REGISTER', entityType: 'user' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await svc.register(req.body.email, req.body.password, req.body.name, req.body.role);
      res.status(201).json(result);
    } catch (err) { next(err); }
  },
);

// POST /auth/login
router.post(
  '/login',
  validateBody(loginSchema),
  auditLog({ action: 'LOGIN', entityType: 'user' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await svc.login(req.body.email, req.body.password);
      res.json(result);
    } catch (err) { next(err); }
  },
);

// POST /auth/refresh
router.post(
  '/refresh',
  validateBody(refreshSchema),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const result = await svc.refresh(req.body.refreshToken);
      res.json(result);
    } catch (err) { next(err); }
  },
);

// POST /auth/logout
router.post(
  '/logout',
  validateBody(refreshSchema),
  authenticate,
  auditLog({ action: 'LOGOUT', entityType: 'user' }),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      await svc.logout(req.body.refreshToken);
      res.status(204).send();
    } catch (err) { next(err); }
  },
);

export default router;
