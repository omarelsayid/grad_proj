// src/modules/payroll/service.ts
import { eq, and } from 'drizzle-orm';
import { db } from '../../db';
import { payroll, employees } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getAll(employeeId?: string, month?: number, year?: number) {
  return db.query.payroll.findMany({
    where: (t, { and: a, eq: e }) => {
      const conds = [];
      if (employeeId) conds.push(e(t.employeeId, employeeId));
      if (month)      conds.push(e(t.month, month));
      if (year)       conds.push(e(t.year, year));
      return conds.length ? a(...conds) : undefined;
    },
    orderBy: (t, { desc }) => [desc(t.year), desc(t.month)],
  });
}

export async function getById(id: string) {
  const row = await db.query.payroll.findFirst({ where: eq(payroll.id, id) });
  if (!row) throw new AppError(404, 'Payroll record not found', 'NOT_FOUND');
  return row;
}

export async function create(data: {
  employeeId: string;
  month: number;
  year: number;
  basicSalary: number;
  allowances?: number;
  deductions?: number;
}) {
  const allowances = data.allowances ?? 0;
  const deductions = data.deductions ?? 0;
  const netSalary  = data.basicSalary + allowances - deductions;

  const id = crypto.randomUUID();
  await db.insert(payroll).values({
    id,
    employeeId:  data.employeeId,
    month:       data.month,
    year:        data.year,
    basicSalary: data.basicSalary,
    allowances,
    deductions,
    netSalary,
    status:      'draft',
  });
  return getById(id);
}

export async function update(id: string, data: Partial<{
  allowances: number;
  deductions: number;
  status: 'draft' | 'processed' | 'paid';
  paidDate: string;
}>) {
  const existing = await getById(id);
  const allowances = data.allowances ?? existing.allowances;
  const deductions = data.deductions ?? existing.deductions;
  const netSalary  = existing.basicSalary + allowances - deductions;

  await db.update(payroll)
    .set({ ...data, netSalary, updatedAt: new Date() })
    .where(eq(payroll.id, id));
  return getById(id);
}

// Generate payroll for all employees for a given month/year
export async function generateMonthly(month: number, year: number) {
  const allEmps = await db.select({ id: employees.id, salary: employees.salary }).from(employees);
  const results = [];

  for (const emp of allEmps) {
    const existing = await db.query.payroll.findFirst({
      where: and(eq(payroll.employeeId, emp.id), eq(payroll.month, month), eq(payroll.year, year)),
    });
    if (!existing) {
      const rec = await create({ employeeId: emp.id, month, year, basicSalary: emp.salary });
      results.push(rec);
    }
  }
  return results;
}
