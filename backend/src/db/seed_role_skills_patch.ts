/**
 * Patch: insert roleRequiredSkills for every job_role that currently has NONE.
 * Looks up skill IDs by NAME so it works with both sk01 and SK001 ID formats.
 *
 * Run with:  npm run db:patch:role-skills
 * Safe to re-run — uses onConflictDoNothing().
 */
import 'dotenv/config';
import { db, connectDB, closeDB } from './index';
import { jobRoles, roleRequiredSkills, skills } from './schema';
import { logger } from '../config/logger';

// ── Skill requirements by TITLE → list of [skillName, minProficiency] ────────
const TITLE_TO_SKILLS: Record<string, [string, number][]> = {
  // ── Engineering ──────────────────────────────────────────────────────────
  'junior software engineer':    [['JavaScript',2],['Node.js',2],['Teamwork',2]],
  'software engineer':           [['JavaScript',3],['Node.js',3],['SQL',2],['Problem Solving',3]],
  'senior software engineer':    [['JavaScript',4],['Node.js',4],['Docker',3],['Agile/Scrum',3],['Problem Solving',4]],
  'frontend developer':          [['JavaScript',4],['React',4],['UI/UX Design',3]],
  'senior frontend developer':   [['JavaScript',4],['React',5],['UI/UX Design',3],['Node.js',2],['Problem Solving',3]],
  'backend developer':           [['Node.js',4],['SQL',3],['Docker',2]],
  'senior backend developer':    [['Node.js',5],['SQL',4],['Docker',3],['DevOps',2]],
  'fullstack developer':         [['JavaScript',4],['Node.js',4],['React',3],['SQL',2]],
  'devops engineer':             [['DevOps',4],['Docker',4],['Kubernetes',3],['Cloud AWS',3]],
  'senior devops engineer':      [['DevOps',5],['Docker',5],['Kubernetes',4],['Cloud AWS',4]],
  'mobile developer':            [['Flutter',4],['Dart',4],['Problem Solving',2]],
  'engineering manager':         [['Project Management',4],['Leadership',4],['Agile/Scrum',4],['Communication',4]],
  'tech lead':                   [['JavaScript',5],['Agile/Scrum',4],['Leadership',4],['Problem Solving',5]],
  'scrum master':                [['Agile/Scrum',5],['Communication',4],['Teamwork',4]],
  'cybersecurity analyst':       [['Cybersecurity',4],['DevOps',3],['Cloud AWS',3]],
  'senior cybersecurity analyst':[['Cybersecurity',5],['DevOps',4],['Cloud AWS',4],['Docker',3]],
  'qa engineer':                 [['Problem Solving',3],['Teamwork',3],['Node.js',2],['JavaScript',2]],

  // ── Data ─────────────────────────────────────────────────────────────────
  'data scientist':              [['Python',4],['Machine Learning',4],['Data Analysis',4],['SQL',3]],
  'senior data scientist':       [['Python',5],['Machine Learning',5],['Deep Learning',4],['Data Analysis',4]],
  'data analyst':                [['SQL',3],['Data Analysis',3],['Python',2]],
  'senior data analyst':         [['SQL',4],['Data Analysis',5],['Python',3],['Machine Learning',2],['Critical Thinking',3]],
  'junior data analyst':         [['SQL',2],['Data Analysis',2]],
  'data engineer':               [['SQL',4],['Python',3],['Docker',3],['DevOps',2]],
  'machine learning engineer':   [['Python',5],['Machine Learning',5],['Deep Learning',3],['SQL',3]],
  'business analyst':            [['Data Analysis',4],['SQL',3],['Project Management',3],['Communication',3]],

  // ── Human Resources ───────────────────────────────────────────────────────
  'hr specialist':               [['HR Management',3],['Recruitment',3],['Communication',3]],
  'hr manager':                  [['HR Management',5],['Leadership',4],['Project Management',4]],
  'recruiter':                   [['Recruitment',4],['Communication',4],['HR Management',2]],
  'hr coordinator':              [['HR Management',2],['Recruitment',2],['Communication',3],['Teamwork',3]],
  'talent acquisition specialist':[['Recruitment',4],['Communication',4],['HR Management',3]],

  // ── Finance ───────────────────────────────────────────────────────────────
  'financial analyst':           [['Finance',4],['Accounting',3],['Data Analysis',3]],
  'accountant':                  [['Finance',3],['Accounting',4],['Data Analysis',2]],
  'senior accountant':           [['Finance',4],['Accounting',5],['Data Analysis',3]],
  'finance manager':             [['Finance',5],['Accounting',4],['Project Management',3],['Leadership',3]],
  'junior accountant':           [['Finance',2],['Accounting',3]],

  // ── Marketing ─────────────────────────────────────────────────────────────
  'marketing specialist':        [['Marketing',4],['Communication',3],['Data Analysis',2]],
  'marketing manager':           [['Marketing',5],['Communication',4],['Project Management',3],['Problem Solving',3]],
  'digital marketing specialist':[['Marketing',4],['Communication',3],['Data Analysis',2]],
  'content specialist':          [['Marketing',3],['Communication',4],['Critical Thinking',3]],
  'brand manager':               [['Marketing',5],['Communication',4],['Project Management',3]],

  // ── Design ───────────────────────────────────────────────────────────────
  'ui/ux designer':              [['UI/UX Design',4],['Communication',3],['Critical Thinking',3]],
  'graphic designer':            [['UI/UX Design',4],['Critical Thinking',3],['Communication',2]],
  'ux researcher':               [['UI/UX Design',3],['Critical Thinking',4],['Communication',4]],

  // ── Product & Management ──────────────────────────────────────────────────
  'product manager':             [['Project Management',5],['Agile/Scrum',4],['Communication',5],['Critical Thinking',4]],
  'project manager':             [['Project Management',5],['Agile/Scrum',4],['Communication',4],['Problem Solving',4]],
  'program manager':             [['Project Management',5],['Leadership',4],['Agile/Scrum',4],['Communication',4]],

  // ── IT Security ───────────────────────────────────────────────────────────
  'it security analyst':         [['Cybersecurity',4],['DevOps',3],['Cloud AWS',3]],
  'network engineer':            [['DevOps',4],['Cloud AWS',3],['Docker',2]],

  // ── Customer Support ─────────────────────────────────────────────────────
  'customer support specialist': [['Communication',5],['Problem Solving',3],['Teamwork',4]],
  'customer success manager':    [['Communication',5],['Problem Solving',4],['Project Management',3],['Teamwork',4]],
  'support engineer':            [['Communication',4],['Problem Solving',3],['Node.js',2],['Teamwork',3]],

  // ── Sales ─────────────────────────────────────────────────────────────────
  'sales representative':        [['Communication',4],['Problem Solving',3],['Teamwork',3]],
  'sales manager':               [['Communication',5],['Project Management',4],['Leadership',3],['Problem Solving',4]],
  'account manager':             [['Communication',4],['Problem Solving',3],['Project Management',3]],

  // ── Operations ───────────────────────────────────────────────────────────
  'operations manager':          [['Project Management',5],['Leadership',4],['Problem Solving',4],['Communication',4]],
  'operations analyst':          [['Data Analysis',3],['SQL',3],['Problem Solving',3],['Communication',2]],
  'logistics coordinator':       [['Project Management',3],['Problem Solving',3],['Communication',3],['Teamwork',3]],
};

const GENERIC_FALLBACK: [string, number][] = [
  ['Communication', 3],
  ['Problem Solving', 3],
  ['Teamwork', 2],
];

function resolveSkillNames(title: string): [string, number][] {
  const key = title.toLowerCase().trim();
  if (TITLE_TO_SKILLS[key]) return TITLE_TO_SKILLS[key]!;
  // Partial match
  for (const [known, reqs] of Object.entries(TITLE_TO_SKILLS)) {
    if (key.includes(known) || known.includes(key)) return reqs;
  }
  return GENERIC_FALLBACK;
}

async function patchRoleSkills() {
  await connectDB();
  logger.info('🔧 Role skills patch starting…');

  // 1. Build name → id map from the actual skills table
  const allSkills = await db.select({ id: skills.id, name: skills.name }).from(skills);
  const nameToId = new Map<string, string>();
  for (const s of allSkills) {
    nameToId.set(s.name.toLowerCase().trim(), s.id);
  }
  logger.info(`Found ${allSkills.length} skills in DB`);

  // 2. Find role IDs that already have at least one requirement
  const coveredRows = await db
    .selectDistinct({ roleId: roleRequiredSkills.roleId })
    .from(roleRequiredSkills);
  const coveredIds = new Set(coveredRows.map((r) => r.roleId));

  // 3. Load all roles
  const allRoles = await db.select({ id: jobRoles.id, title: jobRoles.title }).from(jobRoles);
  const uncovered = allRoles.filter((r) => !coveredIds.has(r.id));

  if (uncovered.length === 0) {
    logger.info('✅  All roles already have skill requirements — nothing to patch');
    await closeDB();
    return;
  }

  logger.info(`Found ${uncovered.length} roles with no skill requirements — patching…`);

  let totalInserted = 0;
  let skipped = 0;

  for (const role of uncovered) {
    const skillPairs = resolveSkillNames(role.title);
    const rows: { roleId: string; skillId: string; minProficiency: number }[] = [];

    for (const [skillName, minProf] of skillPairs) {
      const skillId = nameToId.get(skillName.toLowerCase().trim());
      if (!skillId) {
        logger.warn(`  ⚠  Skill "${skillName}" not found in DB — skipping for role "${role.title}"`);
        skipped++;
        continue;
      }
      rows.push({ roleId: role.id, skillId, minProficiency: minProf });
    }

    if (rows.length === 0) {
      logger.warn(`  ⚠  No resolvable skills for "${role.title}" — skipping`);
      continue;
    }

    await db.insert(roleRequiredSkills).values(rows).onConflictDoNothing();
    totalInserted += rows.length;
    const names = rows.map((r) => {
      const s = allSkills.find((sk) => sk.id === r.skillId);
      return `${s?.name ?? r.skillId}(L${r.minProficiency})`;
    });
    logger.info(`  ✔ "${role.title}" (${role.id}) → [${names.join(', ')}]`);
  }

  logger.info(
    `✅  Patch complete — inserted ${totalInserted} skill requirements across ${uncovered.length} roles` +
    (skipped ? ` (${skipped} skill name lookups skipped)` : ''),
  );
  await closeDB();
}

patchRoleSkills().catch((err) => {
  logger.error('Patch failed:', err);
  process.exit(1);
});
