// src/modules/audit/router.ts
import { Router, Request, Response, NextFunction } from 'express';
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { auditLogs } from '../../db/schema';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';

const router = Router();

// GET /audit — hr_admin only
router.get('/', authenticate, authorize('hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { entityType, userId, limit } = req.query as Record<string, string | undefined>;
      const rows = await db.query.auditLogs.findMany({
        where: (t, { and: a, eq: e }) => {
          const conds = [];
          if (entityType) conds.push(e(t.entityType, entityType));
          if (userId)     conds.push(e(t.userId, userId));
          return conds.length ? a(...conds) : undefined;
        },
        orderBy: (t, { desc }) => [desc(t.createdAt)],
        limit: limit ? parseInt(limit, 10) : 200,
      });
      res.json(rows);
    } catch (err) { next(err); }
  },
);

export default router;
