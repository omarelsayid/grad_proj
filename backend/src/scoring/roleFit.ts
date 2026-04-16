// src/scoring/roleFit.ts — Mirrors Flutter's CalculateRoleFitUseCase exactly
import { eq } from 'drizzle-orm';
import { db } from '../db';
import { employees, employeeSkills, jobRoles, roleRequiredSkills } from '../db/schema';
import { AppError } from '../middleware/errorHandler';

export interface RoleFitResult {
  fitScore:        number;   // 0-100
  matchingSkillIds: string[];
  missingSkillIds:  string[];
}

/**
 * Computes role-fit score for an employee against a role.
 * Algorithm mirrors Flutter's CalculateRoleFitUseCase:
 *   score = Σ min(actual, required) / Σ required * 100
 */
export async function calculateRoleFit(employeeId: string, roleId: string): Promise<RoleFitResult> {
  const [empSkillRows, requirements] = await Promise.all([
    db.select().from(employeeSkills).where(eq(employeeSkills.employeeId, employeeId)),
    db.select().from(roleRequiredSkills).where(eq(roleRequiredSkills.roleId, roleId)),
  ]);

  if (requirements.length === 0) {
    return { fitScore: 100, matchingSkillIds: [], missingSkillIds: [] };
  }

  const skillMap = new Map(empSkillRows.map((s) => [s.skillId, s.proficiency]));

  let totalScore = 0;
  let maxScore   = 0;
  const matching: string[] = [];
  const missing:  string[] = [];

  for (const req of requirements) {
    const actual       = skillMap.get(req.skillId) ?? 0;
    const contribution = Math.min(actual, req.minProficiency);
    totalScore += contribution;
    maxScore   += req.minProficiency;

    if (actual >= req.minProficiency) matching.push(req.skillId);
    else                              missing.push(req.skillId);
  }

  const fitScore = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 100;

  return {
    fitScore: Math.min(Math.max(fitScore, 0), 100),
    matchingSkillIds: matching,
    missingSkillIds:  missing,
  };
}

/**
 * Calculates role fit for ALL roles and returns sorted list.
 */
export async function getMobilityMatches(employeeId: string) {
  const allRoles = await db.select({ id: jobRoles.id, title: jobRoles.title, department: jobRoles.department })
    .from(jobRoles);

  const results = await Promise.all(
    allRoles.map(async (role) => {
      const fit = await calculateRoleFit(employeeId, role.id);
      return { roleId: role.id, roleTitle: role.title, department: role.department, ...fit };
    }),
  );

  return results.sort((a, b) => b.fitScore - a.fitScore);
}
