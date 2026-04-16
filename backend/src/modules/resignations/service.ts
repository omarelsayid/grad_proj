// src/modules/resignations/service.ts
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { resignationRequests, notifications } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getAll(employeeId?: string) {
  return db.query.resignationRequests.findMany({
    where: employeeId ? eq(resignationRequests.employeeId, employeeId) : undefined,
    orderBy: (t, { desc }) => [desc(t.createdAt)],
  });
}

export async function create(employeeId: string, data: {
  lastWorkingDate: string;
  noticePeriodDays?: number;
  reason?: string;
}) {
  // Allow only one active resignation
  const existing = await db.query.resignationRequests.findFirst({
    where: eq(resignationRequests.employeeId, employeeId),
  });
  if (existing && existing.status === 'pending') {
    throw new AppError(409, 'Active resignation already exists', 'DUPLICATE');
  }

  const id = crypto.randomUUID();
  await db.insert(resignationRequests).values({
    id,
    employeeId,
    lastWorkingDate:  data.lastWorkingDate,
    noticePeriodDays: data.noticePeriodDays ?? 30,
    reason:           data.reason ?? '',
    status:           'pending',
  });
  return db.query.resignationRequests.findFirst({ where: eq(resignationRequests.id, id) });
}

export async function updateStatus(id: string, status: 'approved' | 'rejected' | 'withdrawn', approverId?: string) {
  const req = await db.query.resignationRequests.findFirst({ where: eq(resignationRequests.id, id) });
  if (!req) throw new AppError(404, 'Resignation not found', 'NOT_FOUND');

  await db.update(resignationRequests).set({
    status,
    approvedBy: approverId ?? null,
    approvedAt: status !== 'withdrawn' ? new Date() : null,
  }).where(eq(resignationRequests.id, id));

  if (status === 'approved') {
    await db.insert(notifications).values({
      employeeId: req.employeeId,
      title:      'Resignation Approved',
      message:    `Your resignation has been approved. Last working day: ${req.lastWorkingDate}.`,
      type:       'info',
    });
  }

  return db.query.resignationRequests.findFirst({ where: eq(resignationRequests.id, id) });
}
