// src/scoring/skillGaps.ts — Mirrors Flutter's GetOrgSkillGapsUseCase exactly
import { db } from '../db';
import { employees, employeeSkills, jobRoles, roleRequiredSkills, skills } from '../db/schema';

export interface SkillGapEntry {
  skillId:   string;
  skillName: string;
  category:  string;
  demand:    number;    // count of roles requiring this skill
  avgSupply: number;    // avg employee proficiency (0-5)
  gapRatio:  number;    // demand / (avgSupply + 1)
}

/**
 * Computes org-wide skill gaps.
 * Algorithm exactly matches Flutter's GetOrgSkillGapsUseCase.
 */
export async function computeOrgSkillGaps(): Promise<SkillGapEntry[]> {
  const [allSkills, allRequirements, allEmpSkills] = await Promise.all([
    db.select().from(skills),
    db.select().from(roleRequiredSkills),
    db.select().from(employeeSkills),
  ]);

  // Demand: count of roles requiring each skill
  const demand = new Map<string, number>();
  for (const req of allRequirements) {
    demand.set(req.skillId, (demand.get(req.skillId) ?? 0) + 1);
  }

  // Supply: sum and count per skill
  const supplySum   = new Map<string, number>();
  const supplyCount = new Map<string, number>();
  for (const es of allEmpSkills) {
    supplySum.set(es.skillId, (supplySum.get(es.skillId) ?? 0) + es.proficiency);
    supplyCount.set(es.skillId, (supplyCount.get(es.skillId) ?? 0) + 1);
  }

  const entries: SkillGapEntry[] = [];
  for (const skill of allSkills) {
    const d = demand.get(skill.id) ?? 0;
    if (d === 0) continue;

    const sum = supplySum.get(skill.id) ?? 0;
    const cnt = supplyCount.get(skill.id) ?? 0;
    const avgSupply = cnt > 0 ? sum / cnt : 0;

    entries.push({
      skillId:   skill.id,
      skillName: skill.name,
      category:  skill.category,
      demand:    d,
      avgSupply,
      gapRatio:  d / (avgSupply + 1),
    });
  }

  // Sort by demand DESC (mirrors Flutter)
  return entries.sort((a, b) => b.demand - a.demand);
}
