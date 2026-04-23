// src/scoring/roleFit.ts — Importance-weighted role-fit scoring
import { eq } from 'drizzle-orm';
import { db } from '../db';
import { employeeSkills, jobRoles, roleRequiredSkills, skillChains } from '../db/schema';

export interface RoleFitResult {
  fitScore:         number;   // 0-100
  matchingSkillIds: string[];
  missingSkillIds:  string[];
  chainReadiness:   number;   // 0-1: fraction of missing skills with a prereq already held
}

/**
 * Importance-weighted role-fit score:
 *   score = Σ min(actual, required) × weight / Σ required × weight × 100
 *
 * chain_readiness = fraction of missing skills where the employee already holds
 * at least one prerequisite in the skill DAG (matches notebook's chain_readiness feature).
 */
export async function calculateRoleFit(employeeId: string, roleId: string): Promise<RoleFitResult> {
  const [empSkillRows, requirements, chains] = await Promise.all([
    db.select().from(employeeSkills).where(eq(employeeSkills.employeeId, employeeId)),
    db.select().from(roleRequiredSkills).where(eq(roleRequiredSkills.roleId, roleId)),
    db.select({ fromSkillId: skillChains.fromSkillId, toSkillId: skillChains.toSkillId }).from(skillChains),
  ]);

  if (requirements.length === 0) {
    return { fitScore: 100, matchingSkillIds: [], missingSkillIds: [], chainReadiness: 1 };
  }

  const skillMap = new Map(empSkillRows.map(s => [s.skillId, s.proficiency]));

  // prerequisite lookup: target → set of skills that unlock it
  const prereqMap = new Map<string, Set<string>>();
  for (const c of chains) {
    if (!prereqMap.has(c.toSkillId)) prereqMap.set(c.toSkillId, new Set());
    prereqMap.get(c.toSkillId)!.add(c.fromSkillId);
  }

  let weightedScore = 0;
  let maxWeighted   = 0;
  const matching: string[] = [];
  const missing:  string[] = [];

  for (const req of requirements) {
    const actual = skillMap.get(req.skillId) ?? 0;
    const w      = req.importanceWeight ?? 1;
    weightedScore += Math.min(actual, req.minProficiency) * w;
    maxWeighted   += req.minProficiency * w;
    if (actual >= req.minProficiency) matching.push(req.skillId);
    else                              missing.push(req.skillId);
  }

  const fitScore = maxWeighted > 0 ? Math.round((weightedScore / maxWeighted) * 100) : 100;

  const readyCount = missing.filter(sid => {
    const prereqs = prereqMap.get(sid);
    return prereqs && [...prereqs].some(p => (skillMap.get(p) ?? 0) >= 1);
  }).length;
  const chainReadiness = missing.length > 0
    ? Math.round((readyCount / missing.length) * 100) / 100
    : 1;

  return {
    fitScore:         Math.min(Math.max(fitScore, 0), 100),
    matchingSkillIds: matching,
    missingSkillIds:  missing,
    chainReadiness,
  };
}

/** Calculates role fit for ALL roles — used by employee mobility screen. */
export async function getMobilityMatches(employeeId: string) {
  const allRoles = await db
    .select({ id: jobRoles.id, title: jobRoles.title, department: jobRoles.department })
    .from(jobRoles);

  const results = await Promise.all(
    allRoles.map(async role => {
      const fit = await calculateRoleFit(employeeId, role.id);
      return { roleId: role.id, roleTitle: role.title, department: role.department, ...fit };
    }),
  );

  return results.sort((a, b) => b.fitScore - a.fitScore);
}
