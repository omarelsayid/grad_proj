// src/modules/ml/router.ts — Proxy to Python ML service
import { Router, Request, Response, NextFunction } from 'express';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { env } from '../../config/env';
import { AppError } from '../../middleware/errorHandler';

const router = Router();

async function proxyML(path: string, method: 'GET' | 'POST', body?: unknown): Promise<unknown> {
  const url = `${env.ML_SERVICE_URL}${path}`;
  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body:    body ? JSON.stringify(body) : undefined,
      signal:  AbortSignal.timeout(30000),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new AppError(502, `ML service error: ${err}`, 'ML_ERROR');
    }
    return res.json();
  } catch (err) {
    if (err instanceof AppError) throw err;
    throw new AppError(503, 'ML service unavailable', 'ML_UNAVAILABLE');
  }
}

// POST /ml/turnover — hr_admin only
router.post('/turnover', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.json(await proxyML('/predict/turnover', 'POST', req.body)); }
    catch (err) { next(err); }
  },
);

// POST /ml/role-fit — manager + hr_admin
router.post('/role-fit', authenticate, authorize('manager', 'hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.json(await proxyML('/predict/role-fit', 'POST', req.body)); }
    catch (err) { next(err); }
  },
);

// GET /ml/skill-gaps — hr_admin
router.get('/skill-gaps', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.json(await proxyML('/analysis/skill-gaps', 'GET')); }
    catch (err) { next(err); }
  },
);

// POST /ml/learning-path — all roles
router.post('/learning-path', authenticate,
  async (req: Request, res: Response, next: NextFunction) => {
    try { res.json(await proxyML('/recommend/learning-path', 'POST', req.body)); }
    catch (err) { next(err); }
  },
);

// POST /ml/replacements — manager + hr_admin (computed in-process using scoring engine)
router.post('/replacements', authenticate, authorize('manager', 'hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { computeReplacementCandidates } = await import('../../scoring/replacementCandidates');
      res.json(await computeReplacementCandidates(req.body));
    } catch (err) { next(err); }
  },
);

// GET /ml/org-skill-gaps — manager + hr_admin (in-process)
router.get('/org-skill-gaps', authenticate, authorize('manager', 'hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { computeOrgSkillGaps } = await import('../../scoring/skillGaps');
      res.json(await computeOrgSkillGaps());
    } catch (err) { next(err); }
  },
);

export default router;
