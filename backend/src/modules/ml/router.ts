// src/modules/ml/router.ts — Proxy to Python ML service
import { Router, Request, Response, NextFunction } from 'express';
import { eq, gte, and, count } from 'drizzle-orm';
import { authenticate } from '../../middleware/auth';
import { authorize } from '../../middleware/authorize';
import { env } from '../../config/env';
import { AppError } from '../../middleware/errorHandler';
import { db } from '../../db';
import { employees, attendance, leaveRequests } from '../../db/schema';
import { calculateRoleFit } from '../../scoring/roleFit';

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

// GET /ml/turnover/:employeeId
// Auto-fetches all features from DB then calls the ML model — no manual payload needed.
router.get('/turnover/:employeeId', authenticate, authorize('manager', 'hr_admin'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { employeeId } = req.params;

      const [emp] = await db
        .select()
        .from(employees)
        .where(eq(employees.id, employeeId))
        .limit(1);
      if (!emp) throw new AppError(404, 'Employee not found', 'NOT_FOUND');

      // tenure in days
      const tenureDays = emp.joinDate
        ? Math.floor((Date.now() - new Date(emp.joinDate).getTime()) / 86400_000)
        : 0;

      // last 90 days window
      const d90 = new Date(Date.now() - 90 * 86400_000).toISOString().slice(0, 10);
      const d30 = new Date(Date.now() - 30 * 86400_000).toISOString().slice(0, 10);

      // leave requests in last 90 days
      const [{ value: leaveCount }] = await db
        .select({ value: count() })
        .from(leaveRequests)
        .where(and(eq(leaveRequests.employeeId, employeeId), gte(leaveRequests.createdAt, new Date(d90))));

      // attendance in last 30 days
      const attRows = await db
        .select({ status: attendance.status })
        .from(attendance)
        .where(and(eq(attendance.employeeId, employeeId), gte(attendance.date, d30)));

      const lateCount   = attRows.filter(r => r.status === 'late').length;
      const absentCount = attRows.filter(r => r.status === 'absent').length;
      const totalAtt    = attRows.length;
      const absenceRate = totalAtt > 0 ? absentCount / totalAtt : 0;

      const attendanceStatus =
        absenceRate > 0.2 ? 'critical' :
        absenceRate > 0.1 ? 'at_risk'  : 'normal';

      // role-fit score from in-process scoring engine
      const { fitScore } = await calculateRoleFit(employeeId, emp.roleId);

      const payload = {
        employee_id:        employeeId,
        commute_distance_km: emp.commuteDistanceKm,
        tenure_days:         tenureDays,
        role_fit_score:      fitScore,
        absence_rate:        Math.round(absenceRate * 1000) / 1000,
        late_arrivals_30d:   lateCount,
        leave_requests_90d:  leaveCount,
        satisfaction_score:  emp.satisfactionScore,
        attendance_status:   attendanceStatus,
      };

      res.json(await proxyML('/predict/turnover', 'POST', payload));
    } catch (err) { next(err); }
  },
);

// POST /ml/turnover — manual payload (hr_admin only, kept for batch/custom use)
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

// POST /ml/replacements — manager + hr_admin
// Body: { departingEmployeeId, roleId, limit? }
// Returns top N candidates from all 200 employees, scored by weighted fit + chain readiness.
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
