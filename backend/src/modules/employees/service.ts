// src/modules/employees/service.ts
import { eq, ilike, and, or } from 'drizzle-orm';
import { db } from '../../db';
import { employees, employeeSkills, jobRoles, userRoles, users } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

// ── Full employee with skills ──────────────────────────────────────────────────
export async function getAll(department?: string, search?: string) {
  const conditions = [];
  if (department) conditions.push(eq(employees.department, department));
  if (search) {
    conditions.push(
      or(
        ilike(employees.name, `%${search}%`),
        ilike(employees.email, `%${search}%`),
        ilike(employees.currentRole, `%${search}%`),
      ),
    );
  }

  const rows = await db.query.employees.findMany({
    where: conditions.length > 0 ? and(...conditions) : undefined,
    with: { skills: true },
    orderBy: (t, { asc }) => [asc(t.name)],
  });

  return rows.map(toDto);
}

export async function getById(id: string) {
  const row = await db.query.employees.findFirst({
    where: eq(employees.id, id),
    with: { skills: true, jobRole: true },
  });
  if (!row) throw new AppError(404, 'Employee not found', 'NOT_FOUND');
  return toDto(row);
}

export async function getByUserId(userId: string) {
  const row = await db.query.employees.findFirst({
    where: eq(employees.userId, userId),
    with: { skills: true },
  });
  return row ? toDto(row) : null;
}

export async function create(data: {
  id?: string;
  name: string;
  email: string;
  currentRole: string;
  roleId: string;
  department: string;
  joinDate: string;
  salary: number;
  phone?: string;
  commuteDistance?: 'near' | 'moderate' | 'far' | 'very_far';
  satisfactionScore?: number;
}) {
  const id = data.id ?? crypto.randomUUID();

  // Check role exists
  const role = await db.select().from(jobRoles).where(eq(jobRoles.id, data.roleId)).limit(1);
  if (!role[0]) throw new AppError(400, 'Invalid roleId', 'INVALID_ROLE');

  await db.insert(employees).values({
    id,
    name:              data.name,
    email:             data.email.toLowerCase(),
    currentRole:       data.currentRole,
    roleId:            data.roleId,
    department:        data.department,
    joinDate:          data.joinDate,
    salary:            data.salary,
    phone:             data.phone ?? '',
    commuteDistance:   data.commuteDistance ?? 'moderate',
    satisfactionScore: data.satisfactionScore ?? 70,
    avatarUrl:         '',
  });

  return getById(id);
}

export async function update(id: string, data: Partial<{
  name: string;
  currentRole: string;
  roleId: string;
  department: string;
  salary: number;
  phone: string;
  commuteDistance: 'near' | 'moderate' | 'far' | 'very_far';
  satisfactionScore: number;
  avatarUrl: string;
}>) {
  const existing = await db.select({ id: employees.id }).from(employees).where(eq(employees.id, id)).limit(1);
  if (!existing[0]) throw new AppError(404, 'Employee not found', 'NOT_FOUND');

  await db.update(employees)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(employees.id, id));

  return getById(id);
}

export async function remove(id: string) {
  const existing = await db.select({ id: employees.id }).from(employees).where(eq(employees.id, id)).limit(1);
  if (!existing[0]) throw new AppError(404, 'Employee not found', 'NOT_FOUND');
  await db.delete(employees).where(eq(employees.id, id));
}

// ── Skills on an employee ─────────────────────────────────────────────────────
export async function upsertSkill(
  employeeId: string,
  skillId: string,
  proficiency: number,
  lastAssessed: string,
) {
  // Delete old entry if exists, then re-insert (simpler than true upsert across Drizzle versions)
  await db.delete(employeeSkills)
    .where(and(eq(employeeSkills.employeeId, employeeId), eq(employeeSkills.skillId, skillId)));

  await db.insert(employeeSkills).values({ employeeId, skillId, proficiency, lastAssessed });
  return getById(employeeId);
}

// ── DTO — matches Flutter Employee entity shape ────────────────────────────────
type EmpWithSkills = typeof employees.$inferSelect & {
  skills?: (typeof employeeSkills.$inferSelect)[];
};

function toDto(e: EmpWithSkills) {
  return {
    id:                e.id,
    name:              e.name,
    email:             e.email,
    avatarUrl:         e.avatarUrl,
    currentRole:       e.currentRole,
    roleId:            e.roleId,
    department:        e.department,
    joinDate:          e.joinDate,
    salary:            e.salary,
    phone:             e.phone,
    commuteDistance:   e.commuteDistance,
    satisfactionScore: e.satisfactionScore,
    skills: (e.skills ?? []).map((s) => ({
      skillId:      s.skillId,
      proficiency:  s.proficiency,
      lastAssessed: s.lastAssessed,
    })),
  };
}
