// src/scoring/turnoverRisk.ts — Mirrors Flutter's CalculateTurnoverRiskUseCase exactly
import { eq, and, gte, count } from 'drizzle-orm';
import { db } from '../db';
import { employees, attendance, leaveRequests } from '../db/schema';
import { calculateRoleFit } from './roleFit';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface FactorBreakdown {
  factor:    string;
  score:     number;
  maxScore:  number;
  triggered: boolean;
}

export interface TurnoverRiskResult {
  employeeId: string;
  riskScore:  number;       // 0-145 (sum of factor scores)
  riskLevel:  RiskLevel;
  factorBreakdown: FactorBreakdown[];
}

function commuteScore(distance: string): number {
  switch (distance) {
    case 'very_far': return 45;
    case 'far':      return 25;
    case 'moderate': return 10;
    default:         return 0;
  }
}

function bucket(score: number): RiskLevel {
  if (score < 30)  return 'low';
  if (score < 60)  return 'medium';
  if (score < 90)  return 'high';
  return 'critical';
}

export async function calculateTurnoverRisk(employeeId: string): Promise<TurnoverRiskResult> {
  const [empRow, attRows, leavRows] = await Promise.all([
    db.query.employees.findFirst({ where: eq(employees.id, employeeId) }),
    db.query.attendance.findMany({ where: eq(attendance.employeeId, employeeId) }),
    db.query.leaveRequests.findMany({ where: eq(leaveRequests.employeeId, employeeId) }),
  ]);

  if (!empRow) throw new Error(`Employee ${employeeId} not found`);

  const factors: FactorBreakdown[] = [];
  let total = 0;

  // 1. Commute distance (max 45)
  const cs = commuteScore(empRow.commuteDistance);
  factors.push({ factor: 'Commute Distance', score: cs, maxScore: 45, triggered: cs > 0 });
  total += cs;

  // 2. Short tenure < 1yr (max 35)
  const joinMs  = new Date(empRow.joinDate).getTime();
  const tenureYrs = (Date.now() - joinMs) / (365.25 * 86400000);
  const ts = tenureYrs < 1 ? 35 : 0;
  factors.push({ factor: 'Short Tenure (<1yr)', score: ts, maxScore: 35, triggered: ts > 0 });
  total += ts;

  // 3. Low role fit < 60% (max 15)
  let rfs = 0;
  try {
    const fit = await calculateRoleFit(employeeId, empRow.roleId);
    rfs = fit.fitScore < 60 ? 15 : 0;
  } catch { rfs = 0; }
  factors.push({ factor: 'Low Role Fit (<60%)', score: rfs, maxScore: 15, triggered: rfs > 0 });
  total += rfs;

  // 4. Absence rate >= 15% (max 20)
  const absences = attRows.filter((a) => a.status === 'absent').length;
  const absenceRate = attRows.length > 0 ? absences / attRows.length : 0;
  const abs = absenceRate >= 0.15 ? 20 : 0;
  factors.push({ factor: 'High Absence Rate (>=15%)', score: abs, maxScore: 20, triggered: abs > 0 });
  total += abs;

  // 5. Late arrivals >= 6 (max 8)
  const lateCount = attRows.filter((a) => a.status === 'late').length;
  const late = lateCount >= 6 ? 8 : 0;
  factors.push({ factor: 'Frequent Late Arrivals (>=6)', score: late, maxScore: 8, triggered: late > 0 });
  total += late;

  // 6. Low satisfaction < 65 (max 12)
  const sat = empRow.satisfactionScore < 65 ? 12 : 0;
  factors.push({ factor: 'Low Satisfaction (<65)', score: sat, maxScore: 12, triggered: sat > 0 });
  total += sat;

  // 7. Many leave requests >= 5 (max 10)
  const leave = leavRows.length >= 5 ? 10 : 0;
  factors.push({ factor: 'Many Leave Requests (>=5)', score: leave, maxScore: 10, triggered: leave > 0 });
  total += leave;

  return {
    employeeId,
    riskScore: total,
    riskLevel: bucket(total),
    factorBreakdown: factors,
  };
}

/** Calculate risk for all employees (used by nightly cron) */
export async function calculateAllTurnoverRisks(): Promise<TurnoverRiskResult[]> {
  const allEmpIds = await db.select({ id: employees.id }).from(employees);
  return Promise.all(allEmpIds.map((e) => calculateTurnoverRisk(e.id)));
}
