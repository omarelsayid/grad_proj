// src/modules/leaves/service.ts
import { eq, and, desc } from 'drizzle-orm';
import { db } from '../../db';
import { leaveRequests, leaveBalances, notifications } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

function daysBetween(start: string, end: string): number {
  const diff = new Date(end).getTime() - new Date(start).getTime();
  return Math.round(diff / 86400000) + 1;
}

export async function getAll(employeeId?: string, status?: string) {
  return db.query.leaveRequests.findMany({
    where: (t, { and: a, eq: e }) => {
      const conds = [];
      if (employeeId) conds.push(e(t.employeeId, employeeId));
      if (status)     conds.push(e(t.status, status as 'pending' | 'approved' | 'rejected' | 'cancelled'));
      return conds.length ? a(...conds) : undefined;
    },
    orderBy: (t, { desc: d }) => [d(t.createdAt)],
  });
}

export async function getBalances(employeeId: string, year?: number) {
  const y = year ?? new Date().getFullYear();
  return db.query.leaveBalances.findMany({
    where: and(eq(leaveBalances.employeeId, employeeId), eq(leaveBalances.year, y)),
  });
}

export async function create(
  employeeId: string,
  data: { leaveType: string; startDate: string; endDate: string; reason: string },
) {
  const days = daysBetween(data.startDate, data.endDate);
  const year = new Date(data.startDate).getFullYear();

  // Check balance
  const balance = await db.query.leaveBalances.findFirst({
    where: and(
      eq(leaveBalances.employeeId, employeeId),
      eq(leaveBalances.leaveType, data.leaveType as 'annual' | 'sick'),
      eq(leaveBalances.year, year),
    ),
  });

  if (balance && balance.usedDays + days > balance.totalDays) {
    throw new AppError(400, `Insufficient ${data.leaveType} leave balance`, 'INSUFFICIENT_BALANCE');
  }

  const id = crypto.randomUUID();
  await db.insert(leaveRequests).values({
    id,
    employeeId,
    leaveType: data.leaveType as 'annual' | 'sick' | 'compassionate' | 'unpaid',
    startDate: data.startDate,
    endDate:   data.endDate,
    reason:    data.reason,
    status:    'pending',
  });

  return db.query.leaveRequests.findFirst({ where: eq(leaveRequests.id, id) });
}

export async function approve(id: string, approverId: string, approved: boolean) {
  const req = await db.query.leaveRequests.findFirst({ where: eq(leaveRequests.id, id) });
  if (!req) throw new AppError(404, 'Leave request not found', 'NOT_FOUND');
  if (req.status !== 'pending') throw new AppError(409, 'Request already processed', 'ALREADY_PROCESSED');

  const newStatus: 'approved' | 'rejected' = approved ? 'approved' : 'rejected';

  await db.update(leaveRequests).set({
    status:     newStatus,
    approvedBy: approverId,
    approvedAt: new Date(),
  }).where(eq(leaveRequests.id, id));

  // Update balance if approved
  if (approved) {
    const days = daysBetween(req.startDate, req.endDate);
    const year = new Date(req.startDate).getFullYear();
    const bal  = await db.query.leaveBalances.findFirst({
      where: and(
        eq(leaveBalances.employeeId, req.employeeId),
        eq(leaveBalances.leaveType, req.leaveType),
        eq(leaveBalances.year, year),
      ),
    });
    if (bal) {
      await db.update(leaveBalances)
        .set({ usedDays: bal.usedDays + days })
        .where(eq(leaveBalances.id, bal.id));
    }

    // Notify employee
    await db.insert(notifications).values({
      employeeId: req.employeeId,
      title:      'Leave Approved',
      message:    `Your ${req.leaveType} leave (${req.startDate} → ${req.endDate}) has been approved.`,
      type:       'success',
    });
  } else {
    await db.insert(notifications).values({
      employeeId: req.employeeId,
      title:      'Leave Rejected',
      message:    `Your ${req.leaveType} leave request was not approved.`,
      type:       'warning',
    });
  }

  return db.query.leaveRequests.findFirst({ where: eq(leaveRequests.id, id) });
}
