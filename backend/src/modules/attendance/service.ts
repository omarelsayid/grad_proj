// src/modules/attendance/service.ts
import { eq, and, gte, lte, desc } from 'drizzle-orm';
import { db } from '../../db';
import { attendance, employees } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getForEmployee(employeeId: string, from?: string, to?: string) {
  const conditions = [eq(attendance.employeeId, employeeId)];
  if (from) conditions.push(gte(attendance.date, from));
  if (to)   conditions.push(lte(attendance.date, to));

  return db.query.attendance.findMany({
    where: and(...conditions),
    orderBy: (t, { desc: d }) => [d(t.date)],
  });
}

export async function getAll(from?: string, to?: string, department?: string) {
  const empIds = department
    ? (await db.select({ id: employees.id }).from(employees).where(eq(employees.department, department))).map((e) => e.id)
    : [];

  const rows = await db.query.attendance.findMany({
    where: (t, { and: a, gte: g, lte: l, inArray }) => {
      const conds = [];
      if (from) conds.push(g(t.date, from));
      if (to)   conds.push(l(t.date, to));
      if (empIds.length) conds.push(inArray(t.employeeId, empIds));
      return conds.length ? a(...conds) : undefined;
    },
    with: { employee: false } as never,
    orderBy: (t, { desc: d }) => [d(t.date)],
  });
  return rows;
}

export async function checkIn(employeeId: string) {
  const today  = new Date().toISOString().slice(0, 10);
  const checkInTime = new Date().toTimeString().slice(0, 5);

  const existing = await db.query.attendance.findFirst({
    where: and(eq(attendance.employeeId, employeeId), eq(attendance.date, today)),
  });

  if (existing?.checkIn) throw new AppError(409, 'Already checked in today', 'ALREADY_CHECKED_IN');

  const id = crypto.randomUUID();
  if (existing) {
    await db.update(attendance).set({ checkIn: checkInTime }).where(eq(attendance.id, existing.id));
    return { ...existing, checkIn: checkInTime };
  }

  await db.insert(attendance).values({ id, employeeId, date: today, checkIn: checkInTime, status: 'present', type: 'office' });
  return db.query.attendance.findFirst({ where: eq(attendance.id, id) });
}

export async function checkOut(employeeId: string) {
  const today       = new Date().toISOString().slice(0, 10);
  const checkOutTime = new Date().toTimeString().slice(0, 5);

  const existing = await db.query.attendance.findFirst({
    where: and(eq(attendance.employeeId, employeeId), eq(attendance.date, today)),
  });

  if (!existing) throw new AppError(400, 'No check-in found for today', 'NOT_CHECKED_IN');
  if (existing.checkOut) throw new AppError(409, 'Already checked out today', 'ALREADY_CHECKED_OUT');

  await db.update(attendance).set({ checkOut: checkOutTime }).where(eq(attendance.id, existing.id));
  return { ...existing, checkOut: checkOutTime };
}
