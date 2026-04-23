// src/db/seed_ml.ts
// Check-first CSV seeder: reads Data/ folder and populates 200 employees + all
// reference data. Run with:  npm run db:seed:ml
// Use --force to wipe existing employees and re-seed from CSV.
import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import bcrypt from 'bcryptjs';
import { eq, sql } from 'drizzle-orm';
import { db, connectDB, closeDB } from './index';
import {
  departments, jobRoles, skills, skillChains, roleRequiredSkills,
  employees, employeeSkills, attendance, leaveBalances, leaveRequests,
  payroll, learningItems, users, userRoles,
} from './schema';
import { logger } from '../config/logger';

const DATA_DIR = path.resolve(__dirname, '../../../Data');
const FORCE    = process.argv.includes('--force');

// ── CSV parser ────────────────────────────────────────────────────────────────
function parseCSV(filename: string): Record<string, string>[] {
  const raw   = fs.readFileSync(path.join(DATA_DIR, filename), 'utf-8');
  const lines = raw.replace(/\r/g, '').trim().split('\n').filter(l => l.trim() !== '');
  const headers = parseLine(lines[0]!);
  return lines.slice(1).map(l => {
    const vals = parseLine(l);
    return Object.fromEntries(headers.map((h, i) => [h, (vals[i] ?? '').trim()]));
  });
}

function parseLine(line: string): string[] {
  const out: string[] = [];
  let cur = ''; let inQ = false;
  for (const ch of line) {
    if (ch === '"') { inQ = !inQ; continue; }
    if (ch === ',' && !inQ) { out.push(cur.trim()); cur = ''; continue; }
    cur += ch;
  }
  out.push(cur.trim());
  return out;
}

// ── ID normalizers ────────────────────────────────────────────────────────────
// attendance_summary / leave_requests / payroll use EMP-0001; skill matrix uses EMP0001
const normalizeEmpId  = (id: string) => id.replace('EMP-', 'EMP');
const deptId          = (n: string)  => `DEPT-${n}`;
const roleId          = (n: string)  => `JR-${n}`;

// ── Category mappers ──────────────────────────────────────────────────────────
function mapSkillCat(cat: string): 'technical' | 'management' | 'soft' | 'domain' {
  const c = cat.toLowerCase();
  if (c.includes('management') || c.includes('business') || c.includes('product')) return 'management';
  if (c.includes('soft') || c.includes('communication') || c.includes('interpersonal')) return 'soft';
  if (c.includes('domain') || c.includes('finance') || c.includes('marketing') || c.includes('sales') || c.includes('hr')) return 'domain';
  return 'technical';
}

function mapRoleLevel(level: string): 'junior' | 'mid' | 'senior' | 'lead' | 'manager' {
  switch (level.toLowerCase().trim()) {
    case 'junior': case 'entry': return 'junior';
    case 'senior':               return 'senior';
    case 'lead':                 return 'lead';
    case 'manager': case 'director': return 'manager';
    default:                     return 'mid';
  }
}

function mapCommute(cat: string): 'near' | 'moderate' | 'far' | 'very_far' {
  switch (cat.toLowerCase().trim()) {
    case 'near':                    return 'near';
    case 'medium': case 'moderate': return 'moderate';
    case 'far':                     return 'far';
    case 'very far': case 'very_far': return 'very_far';
    default:                        return 'moderate';
  }
}

function mapLeaveType(lt: string): 'annual' | 'sick' | 'compassionate' | 'unpaid' | 'maternity' | 'paternity' {
  const l = lt.toLowerCase();
  if (l.includes('annual'))       return 'annual';
  if (l.includes('sick'))         return 'sick';
  if (l.includes('compassion'))   return 'compassionate';
  if (l.includes('unpaid'))       return 'unpaid';
  if (l.includes('matern'))       return 'maternity';
  if (l.includes('patern'))       return 'paternity';
  return 'annual';
}

function mapLeaveStatus(s: string): 'pending' | 'approved' | 'rejected' | 'cancelled' {
  switch (s.toLowerCase().trim()) {
    case 'approved':  return 'approved';
    case 'rejected':  return 'rejected';
    case 'cancelled': case 'canceled': return 'cancelled';
    default:          return 'pending';
  }
}

function mapLearningType(t: string): 'course' | 'certification' | 'mentorship' | 'project' | 'book' {
  switch (t.toLowerCase().trim()) {
    case 'certification': return 'certification';
    case 'mentorship':    return 'mentorship';
    case 'project':       return 'project';
    case 'book':          return 'book';
    default:              return 'course';
  }
}

// ── Guard: skip if already seeded with CSV data ───────────────────────────────
async function isSeeded(): Promise<boolean> {
  const [row] = await db
    .select({ id: employees.id })
    .from(employees)
    .where(eq(employees.id, 'EMP0001'))
    .limit(1);
  return !!row;
}

// ── Batch insert helper ───────────────────────────────────────────────────────
async function batch<T extends object>(table: Parameters<typeof db.insert>[0], rows: T[], size = 100) {
  for (let i = 0; i < rows.length; i += size) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (db.insert(table) as any).values(rows.slice(i, i + size)).onConflictDoNothing();
  }
}

// ── 1. Departments ────────────────────────────────────────────────────────────
async function seedDepartments() {
  const rows = parseCSV('departments.csv');
  const vals = rows.map(r => ({
    id:          deptId(r['department_id']!),
    name:        r['department_name']!,
    description: '',
  }));
  await batch(departments, vals);
  logger.info(`  ✔ ${vals.length} departments`);
}

// ── 2. Job Roles ──────────────────────────────────────────────────────────────
async function seedJobRoles() {
  const rows = parseCSV('job_roles.csv');
  const vals = rows.map(r => ({
    id:          roleId(r['job_role_id']!),
    title:       r['role_name']!,
    department:  r['department_id']!,          // department name resolved later via join; kept as raw id for now
    level:       mapRoleLevel(r['level']!),
    description: '',
  }));

  // Resolve department names
  const depts = parseCSV('departments.csv');
  const deptMap = Object.fromEntries(depts.map(d => [d['department_id']!, d['department_name']!]));
  const resolved = vals.map(v => ({ ...v, department: deptMap[v.department] ?? v.department }));

  await batch(jobRoles, resolved);
  logger.info(`  ✔ ${resolved.length} job roles`);
}

// ── 3. Skills ─────────────────────────────────────────────────────────────────
async function seedSkills() {
  const rows = parseCSV('skills_catalog.csv');
  const vals = rows.map(r => ({
    id:          r['skill_id']!,
    name:        r['skill_name']!,
    category:    mapSkillCat(r['category']!),
    description: r['category']!,
  }));
  await batch(skills, vals);
  logger.info(`  ✔ ${vals.length} skills`);
}

// ── 4. Skill Chains (DAG) ─────────────────────────────────────────────────────
async function seedSkillChains() {
  const rows = parseCSV('skill_chain_dag.csv');
  const vals = rows.map(r => ({
    id:          crypto.randomUUID(),
    fromSkillId: r['prerequisite_skill_id']!,
    toSkillId:   r['target_skill_id']!,
    description: `${r['prerequisite_skill_name']} → ${r['target_skill_name']}`,
    edgeWeight:  parseFloat(r['edge_weight'] ?? '1') || 1.0,
  }));
  await batch(skillChains, vals);
  logger.info(`  ✔ ${vals.length} skill chain edges`);
}

// ── 5. Role Required Skills (with importance weights) ─────────────────────────
async function seedRoleRequirements() {
  const rows = parseCSV('job_role_requirements.csv');
  // job_role_requirements.csv uses different numbering than job_roles.csv — match by name
  const jobRoleRows = parseCSV('job_roles.csv');
  const nameToJRId: Record<string, string> = Object.fromEntries(
    jobRoleRows.map(r => [r['role_name']!.toLowerCase().trim(), roleId(r['job_role_id']!)])
  );

  const vals = rows
    .map(r => {
      const roleName = (r['job_role_name'] ?? '').toLowerCase().trim();
      const rid = nameToJRId[roleName];
      if (!rid) return null; // no matching role in job_roles.csv — skip
      return {
        id:               crypto.randomUUID(),
        roleId:           rid,
        skillId:          r['skill_id']!,
        minProficiency:   parseInt(r['min_proficiency'] ?? '1', 10) || 1,
        importanceWeight: parseFloat(r['importance_weight'] ?? '1') || 1.0,
      };
    })
    .filter((v): v is NonNullable<typeof v> => v !== null);

  await batch(roleRequiredSkills, vals);
  logger.info(`  ✔ ${vals.length} role requirements (name-matched)`);
}

// ── 6. Employees (200 from CSV) ───────────────────────────────────────────────
async function seedEmployees() {
  const rows = parseCSV('employees_core.csv');
  const depts = parseCSV('departments.csv');
  const roles = parseCSV('job_roles.csv');
  const deptMap = Object.fromEntries(depts.map(d => [d['department_id']!, d['department_name']!]));
  const roleMap = Object.fromEntries(roles.map(r => [r['job_role_id']!, r['role_name']!]));

  const vals = rows.map(r => {
    const deptName = deptMap[r['department_id']!] ?? r['department_id']!;
    const roleName = roleMap[r['job_role_id']!]   ?? r['job_role_id']!;
    return {
      id:                normalizeEmpId(r['employee_id']!),
      name:              r['full_name']!,
      email:             `${normalizeEmpId(r['employee_id']!).toLowerCase()}@skillsync.dev`,
      avatarUrl:         '',
      currentRole:       roleName,
      roleId:            roleId(r['job_role_id']!),
      department:        deptName,
      joinDate:          r['hire_date']!,
      salary:            parseFloat(r['salary_egp'] ?? '0') || 0,
      phone:             r['phone_number'] ?? '',
      commuteDistance:   mapCommute(r['commute_category']!),
      commuteDistanceKm: parseFloat(r['commute_distance_km'] ?? '0') || 0,
      satisfactionScore: 70, // derived from evaluations later; default 70
    };
  });

  await batch(employees, vals);
  logger.info(`  ✔ ${vals.length} employees`);
  return vals;
}

// ── 7. Employee Skills ────────────────────────────────────────────────────────
async function seedEmployeeSkills() {
  const rows = parseCSV('employee_skill_matrix.csv');
  const vals = rows.map(r => ({
    id:           crypto.randomUUID(),
    employeeId:   normalizeEmpId(r['employee_id']!),
    skillId:      r['skill_id']!,
    proficiency:  parseInt(r['proficiency'] ?? '1', 10) || 1,
    lastAssessed: '2024-01-01',
  }));
  await batch(employeeSkills, vals);
  logger.info(`  ✔ ${vals.length} employee-skill entries`);
}

// ── 8. Leave Balances (annual + sick + compassionate for all employees) ────────
async function seedLeaveBalances(empIds: string[]) {
  const year = new Date().getFullYear();
  const vals = empIds.flatMap(id => [
    { id: crypto.randomUUID(), employeeId: id, leaveType: 'annual'       as const, totalDays: 21, usedDays: 0, year },
    { id: crypto.randomUUID(), employeeId: id, leaveType: 'sick'         as const, totalDays: 10, usedDays: 0, year },
    { id: crypto.randomUUID(), employeeId: id, leaveType: 'compassionate'as const, totalDays: 5,  usedDays: 0, year },
  ]);
  await batch(leaveBalances, vals);
  logger.info(`  ✔ ${vals.length} leave balance rows`);
}

// ── 9. Leave Requests ─────────────────────────────────────────────────────────
async function seedLeaveRequests(validEmpIds: Set<string>) {
  const rows = parseCSV('leave_requests.csv');
  const vals = rows
    .map(r => {
      const empId = normalizeEmpId(r['employee_id']!);
      if (!validEmpIds.has(empId)) return null;
      return {
        id:         r['request_id']!,
        employeeId: empId,
        leaveType:  mapLeaveType(r['leave_type']!),
        startDate:  r['start_date']!,
        endDate:    r['end_date']!,
        reason:     '',
        status:     mapLeaveStatus(r['status']!),
        approvedBy: null as string | null,
        approvedAt: null as Date | null,
      };
    })
    .filter((v): v is NonNullable<typeof v> => v !== null);

  await batch(leaveRequests, vals);
  logger.info(`  ✔ ${vals.length} leave requests`);
}

// ── 10. Payroll (all months from CSV) ─────────────────────────────────────────
async function seedPayroll(validEmpIds: Set<string>) {
  const rows = parseCSV('monthly_payroll.csv');
  const vals = rows
    .map(r => {
      const empId = normalizeEmpId(r['employee_id']!);
      if (!validEmpIds.has(empId)) return null;

      // month format: "2024-06"
      const parts = (r['month'] ?? '').split('-');
      const yr    = parseInt(parts[0] ?? '2024', 10);
      const mo    = parseInt(parts[1] ?? '1', 10);

      const base       = parseFloat(r['base_salary']   ?? '0') || 0;
      const bonus      = parseFloat(r['bonus_amount']  ?? '0') || 0;
      const otPay      = parseFloat(r['overtime_pay']  ?? '0') || 0;
      const deductions = parseFloat(r['total_deductions'] ?? '0') || 0;
      const net        = parseFloat(r['total_salary']  ?? '0') || (base + bonus + otPay - deductions);

      return {
        id:          r['payroll_id']!,
        employeeId:  empId,
        month:       mo,
        year:        yr,
        basicSalary: base,
        allowances:  bonus + otPay,
        deductions,
        netSalary:   net,
        status:      'paid' as const,
        paidDate:    null as string | null,
      };
    })
    .filter((v): v is NonNullable<typeof v> => v !== null);

  await batch(payroll, vals, 200);
  logger.info(`  ✔ ${vals.length} payroll records`);
}

// ── 11. Learning Items ────────────────────────────────────────────────────────
async function seedLearningItems() {
  const rows = parseCSV('learning_resources.csv');
  const vals = rows.map(r => ({
    id:          r['resource_id']!,
    title:       r['title']!,
    skillId:     r['target_skill_id'] || null,
    type:        mapLearningType(r['type']!),
    url:         '',
    durationHrs: parseFloat(r['duration_hours'] ?? '0') || 0,
    priority:    (['high', 'medium', 'low', 'urgent'].includes((r['priority'] ?? '').toLowerCase())
                   ? r['priority']!.toLowerCase()
                   : 'medium') as 'high' | 'medium' | 'low' | 'urgent',
    description: r['category'] ?? '',
  }));
  await batch(learningItems, vals);
  logger.info(`  ✔ ${vals.length} learning items`);
}

// ── 12. Attendance ────────────────────────────────────────────────────────────
async function seedAttendance(empIdSet: Set<string>) {
  const rows = parseCSV('attendance.csv');
  type AttStatus = 'present' | 'absent' | 'late' | 'half_day' | 'remote';
  const statusMap: Record<string, AttStatus> = {
    present: 'present', absent: 'absent', late: 'late',
    'half day': 'half_day', half_day: 'half_day', remote: 'remote',
  };

  const vals = rows
    .map(r => {
      const empId = normalizeEmpId(r['employee_id']!);
      if (!empIdSet.has(empId)) return null;
      const statusRaw = (r['status'] ?? '').toLowerCase();
      const status: AttStatus = statusMap[statusRaw] ?? 'present';
      return {
        id:         `${empId}-${r['date']!}`,
        employeeId: empId,
        date:       r['date']!,
        checkIn:    r['check_in_time'] || null,
        checkOut:   r['check_out_time'] || null,
        status,
        type:       'office' as const,
        notes:      r['absence_reason'] ?? '',
      };
    })
    .filter((v): v is NonNullable<typeof v> => v !== null);

  await batch(attendance, vals, 500);
  logger.info(`  ✔ ${vals.length} attendance records`);
}

// ── 13. Demo Users ────────────────────────────────────────────────────────────
// EMP0201/0202/0203 are real rows added to the CSV files — names + skills match the notebook data.
async function seedDemoUsers(_empRows: Record<string, string>[]) {
  const demo = [
    { empId: 'EMP0201', role: 'employee' as const, email: 'ahmed.hassan@skillsync.dev',  password: 'Employee@123' },
    { empId: 'EMP0202', role: 'manager'  as const, email: 'tarek.mansour@skillsync.dev', password: 'Manager@123'  },
    { empId: 'EMP0203', role: 'hr_admin' as const, email: 'rana.essam@skillsync.dev',    password: 'Admin@123'    },
  ];

  for (const { empId, role, email, password } of demo) {
    const hash = await bcrypt.hash(password, 12);
    const uid  = crypto.randomUUID();

    await db.insert(users).values({ id: uid, email, passwordHash: hash }).onConflictDoNothing();

    const [existing] = await db.select({ id: users.id }).from(users).where(eq(users.email, email));
    if (!existing) continue;
    const userId = existing.id;

    await db.insert(userRoles).values({ userId, role }).onConflictDoNothing();
    // Link the user to their employee record (name/email already correct in CSV)
    await db.update(employees).set({ userId }).where(eq(employees.id, empId));

    logger.info(`  ✔ demo user ${email} → ${empId} (${role})`);
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function seed() {
  await connectDB();

  if (!FORCE && await isSeeded()) {
    logger.info('⏭  Database already has CSV employees — skipping seed. Use --force to re-seed.');
    await closeDB();
    return;
  }

  if (FORCE) {
    logger.info('⚠️  --force: truncating employees and dependents...');
    await db.execute(sql`
      TRUNCATE TABLE payroll, leave_requests, leave_balances,
                     attendance, employee_skills, employees,
                     role_required_skills, skill_chains,
                     learning_items, skills,
                     job_roles, departments
      RESTART IDENTITY CASCADE
    `);
  }

  logger.info('🌱 Starting ML CSV seed...');

  await seedDepartments();
  await seedJobRoles();
  await seedSkills();
  await seedSkillChains();
  await seedRoleRequirements();

  const empRows = parseCSV('employees_core.csv');
  await seedEmployees();

  const empIds    = empRows.map(r => normalizeEmpId(r['employee_id']!));
  const empIdSet  = new Set(empIds);

  await seedEmployeeSkills();
  await seedAttendance(empIdSet);
  await seedLeaveBalances(empIds);
  await seedLeaveRequests(empIdSet);
  await seedPayroll(empIdSet);
  await seedLearningItems();
  await seedDemoUsers(empRows);

  logger.info(`🎉 CSV seed complete — ${empIds.length} employees loaded.`);
  await closeDB();
}

seed().catch(err => {
  logger.error('Seed failed', { error: (err as Error).message });
  process.exit(1);
});
