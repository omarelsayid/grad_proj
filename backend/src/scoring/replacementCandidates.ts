// src/scoring/replacementCandidates.ts — Mirrors Flutter's FindReplacementCandidatesUseCase
import { eq, ne } from 'drizzle-orm';
import { db } from '../db';
import { employees } from '../db/schema';
import { calculateRoleFit, RoleFitResult } from './roleFit';

export interface ReplacementCandidate {
  employee: {
    id:          string;
    name:        string;
    currentRole: string;
    department:  string;
  };
  fitScore:        number;
  matchingSkillIds: string[];
  missingSkillIds:  string[];
}

export interface ReplacementRequest {
  departingEmployeeId: string;
  roleId:              string;
  limit?:              number;
}

export async function computeReplacementCandidates(
  req: ReplacementRequest,
): Promise<ReplacementCandidate[]> {
  const { departingEmployeeId, roleId, limit = 5 } = req;

  // Get all employees except the departing one
  const candidates = await db.select({
    id:          employees.id,
    name:        employees.name,
    currentRole: employees.currentRole,
    department:  employees.department,
  }).from(employees).where(ne(employees.id, departingEmployeeId));

  // Score each candidate
  const scored = await Promise.all(
    candidates.map(async (emp) => {
      const fit = await calculateRoleFit(emp.id, roleId);
      return { employee: emp, ...fit };
    }),
  );

  // Sort by fitScore DESC, take top N
  return scored
    .sort((a, b) => b.fitScore - a.fitScore)
    .slice(0, limit);
}
