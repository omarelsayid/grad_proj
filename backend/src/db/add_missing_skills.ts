/**
 * One-time: insert the handful of skills that seed_ml.ts skipped.
 * Run with: npm run db:add-missing-skills
 */
import 'dotenv/config';
import { db, connectDB, closeDB } from './index';
import { skills, roleRequiredSkills, jobRoles } from './schema';
import { logger } from '../config/logger';

const MISSING_SKILLS = [
  { id: 'sk-agile',     name: 'Agile/Scrum',   category: 'management' as const, description: 'Agile methodologies and Scrum framework' },
  { id: 'sk-marketing', name: 'Marketing',      category: 'domain'     as const, description: 'Digital and traditional marketing' },
  { id: 'sk-finance',   name: 'Finance',        category: 'domain'     as const, description: 'Financial analysis and management' },
];

// Roles that need the newly added skills filled in
const ROLE_SKILL_ADDITIONS: { title: string; skillName: string; minProficiency: number }[] = [
  { title: 'tech lead',            skillName: 'Agile/Scrum', minProficiency: 4 },
  { title: 'scrum master',         skillName: 'Agile/Scrum', minProficiency: 5 },
  { title: 'marketing specialist', skillName: 'Marketing',   minProficiency: 4 },
  { title: 'marketing manager',    skillName: 'Marketing',   minProficiency: 5 },
  { title: 'financial analyst',    skillName: 'Finance',     minProficiency: 4 },
  { title: 'accountant',           skillName: 'Finance',     minProficiency: 3 },
  { title: 'finance manager',      skillName: 'Finance',     minProficiency: 5 },
];

async function run() {
  await connectDB();

  // 1. Insert missing skills
  for (const s of MISSING_SKILLS) {
    await db.insert(skills).values(s).onConflictDoNothing();
    logger.info(`  ✔ Skill "${s.name}" (${s.id}) ensured`);
  }

  // 2. Build lookup maps
  const allSkills = await db.select({ id: skills.id, name: skills.name }).from(skills);
  const nameToId = new Map(allSkills.map((s) => [s.name.toLowerCase().trim(), s.id]));

  const allRoles = await db.select({ id: jobRoles.id, title: jobRoles.title }).from(jobRoles);
  const titleToIds = new Map<string, string[]>();
  for (const r of allRoles) {
    const key = r.title.toLowerCase().trim();
    const existing = titleToIds.get(key) ?? [];
    existing.push(r.id);
    titleToIds.set(key, existing);
  }

  // 3. Insert the missing role-skill links
  let inserted = 0;
  for (const { title, skillName, minProficiency } of ROLE_SKILL_ADDITIONS) {
    const skillId = nameToId.get(skillName.toLowerCase().trim());
    const roleIds = titleToIds.get(title.toLowerCase().trim()) ?? [];

    if (!skillId) { logger.warn(`Skill "${skillName}" not found after insert — skip`); continue; }
    if (roleIds.length === 0) { logger.warn(`Role "${title}" not found in DB — skip`); continue; }

    for (const roleId of roleIds) {
      await db
        .insert(roleRequiredSkills)
        .values({ roleId, skillId, minProficiency })
        .onConflictDoNothing();
      inserted++;
      logger.info(`  ✔ "${title}" (${roleId}) ← ${skillName} L${minProficiency}`);
    }
  }

  logger.info(`✅  Done — ${inserted} links inserted`);
  await closeDB();
}

run().catch((e) => { logger.error(e); process.exit(1); });
