// src/modules/skills/service.ts
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { skills, skillChains, relatedSkills, roleRequiredSkills, jobRoles } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getAllSkills() {
  const rows = await db.query.skills.findMany({ orderBy: (t, { asc }) => [asc(t.name)] });
  return rows;
}

export async function getSkillById(id: string) {
  const row = await db.query.skills.findFirst({ where: eq(skills.id, id) });
  if (!row) throw new AppError(404, 'Skill not found', 'NOT_FOUND');
  return row;
}

export async function getAllRoles() {
  const roles = await db.query.jobRoles.findMany({
    with: { requiredSkills: true },
    orderBy: (t, { asc }) => [asc(t.department), asc(t.title)],
  });
  return roles.map((r) => ({
    id:          r.id,
    title:       r.title,
    department:  r.department,
    level:       r.level,
    description: r.description,
    requiredSkills: r.requiredSkills.map((rs) => ({
      skillId:       rs.skillId,
      minProficiency: rs.minProficiency,
    })),
  }));
}

export async function getRoleById(id: string) {
  const row = await db.query.jobRoles.findFirst({
    where: eq(jobRoles.id, id),
    with: { requiredSkills: true },
  });
  if (!row) throw new AppError(404, 'Role not found', 'NOT_FOUND');
  return {
    id: row.id, title: row.title, department: row.department,
    level: row.level, description: row.description,
    requiredSkills: row.requiredSkills.map((rs) => ({
      skillId: rs.skillId, minProficiency: rs.minProficiency,
    })),
  };
}

export async function getAllSkillChains() {
  return db.query.skillChains.findMany();
}

export async function createSkill(data: {
  id?: string;
  name: string;
  category: 'technical' | 'management' | 'soft' | 'domain';
  description?: string;
}) {
  const id = data.id ?? crypto.randomUUID();
  await db.insert(skills).values({
    id,
    name:        data.name,
    category:    data.category,
    description: data.description ?? '',
  });
  return getSkillById(id);
}

export async function createRole(data: {
  id?: string;
  title: string;
  department: string;
  level: 'junior' | 'mid' | 'senior' | 'lead' | 'manager';
  description?: string;
  requiredSkills?: { skillId: string; minProficiency: number }[];
}) {
  const id = data.id ?? crypto.randomUUID();
  await db.insert(jobRoles).values({
    id, title: data.title, department: data.department,
    level: data.level, description: data.description ?? '',
  });

  if (data.requiredSkills?.length) {
    await db.insert(roleRequiredSkills).values(
      data.requiredSkills.map((rs) => ({ roleId: id, skillId: rs.skillId, minProficiency: rs.minProficiency })),
    );
  }
  return getRoleById(id);
}
