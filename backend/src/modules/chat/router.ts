// src/modules/chat/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';
import { authenticate } from '../../middleware/auth';
import { validateBody } from '../../middleware/validateBody';
import * as svc from './service';

const router = Router();

// GET /chat/history
router.get('/history', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user!.employeeId) return res.json([]);
    const limit = req.query['limit'] ? parseInt(req.query['limit'] as string, 10) : 50;
    res.json(await svc.getHistory(req.user!.employeeId, limit));
  } catch (err) { next(err); }
});

// POST /chat/ask — send question to AI
router.post('/ask', authenticate,
  validateBody(z.object({ question: z.string().min(1) })),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user!.employeeId) return res.status(400).json({ error: 'No employee profile' });
      const answer = await svc.askAI(req.user!.employeeId, req.body.question);
      res.json({ answer });
    } catch (err) { next(err); }
  },
);

export default router;
