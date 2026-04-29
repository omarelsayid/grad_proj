/**
 * fix_role_skill_gaps.ts
 *
 * Ensures every employee has at least the minimum required proficiency
 * for each skill their job role demands.
 *
 * - If the employee has no entry for a required skill → INSERT at minProficiency
 * - If they have it but below minProficiency → UPDATE to minProficiency
 * - Skills already at or above min are untouched
 *
 * Run with: npm run db:fix-role-skills
 */
import 'dotenv/config';
import { and, eq, inArray } from 'drizzle-orm';
import { db, connectDB, closeDB } from './index';
import { employees, employeeSkills, jobRoles, roleRequiredSkills } from './schema';
import { logger } from '../config/logger';

async function run() {
  await connectDB();
  logger.info('🔧 Fixing employee role-skill gaps…');

  // 1. Load all role requirements: roleId → [{skillId, minProficiency}]
  const reqs = await db
    .select({
      roleId:         roleRequiredSkills.roleId,
      skillId:        roleRequiredSkills.skillId,
      minProficiency: roleRequiredSkills.minProficiency,
    })
    .from(roleRequiredSkills);

  const reqsByRole = new Map<string, { skillId: string; min: number }[]>();
  for (const r of reqs) {
    if (!reqsByRole.has(r.roleId)) reqsByRole.set(r.roleId, []);
    reqsByRole.get(r.roleId)!.push({ skillId: r.skillId, min: r.minProficiency });
  }

  // 2. Load all employees (id, roleId)
  const allEmps = await db
    .select({ id: employees.id, roleId: employees.roleId })
    .from(employees);

  // 3. For each employee, check & fix missing/low skills
  let inserted = 0;
  let updated  = 0;

  for (const emp of allEmps) {
    const roleReqs = reqsByRole.get(emp.roleId);
    if (!roleReqs || roleReqs.length === 0) continue;

    const skillIds = roleReqs.map(r => r.skillId);

    // Load current skills for this employee for the relevant skills only
    const current = await db
      .select({ skillId: employeeSkills.skillId, proficiency: employeeSkills.proficiency, id: employeeSkills.id })
      .from(employeeSkills)
      .where(
        and(
          eq(employeeSkills.employeeId, emp.id),
          inArray(employeeSkills.skillId, skillIds),
        ),
      );

    const currentMap = new Map(current.map(c => [c.skillId, c]));

    for (const req of roleReqs) {
      const existing = currentMap.get(req.skillId);

      if (!existing) {
        // Missing entirely — insert at minimum
        await db.insert(employeeSkills).values({
          id:           crypto.randomUUID(),
          employeeId:   emp.id,
          skillId:      req.skillId,
          proficiency:  req.min,
          lastAssessed: '2024-01-01',
        }).onConflictDoNothing();
        inserted++;
      } else if (existing.proficiency < req.min) {
        // Below minimum — bump to minimum
        await db
          .update(employeeSkills)
          .set({ proficiency: req.min })
          .where(eq(employeeSkills.id, existing.id));
        updated++;
      }
    }
  }

  logger.info(`✅  Done — ${inserted} skills inserted, ${updated} skills updated across ${allEmps.length} employees`);
  await closeDB();
}

run().catch(e => { logger.error(e); process.exit(1); });
