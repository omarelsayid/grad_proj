// src/modules/notifications/service.ts
import { eq, and } from 'drizzle-orm';
import { db } from '../../db';
import { notifications } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getAll(employeeId: string) {
  return db.query.notifications.findMany({
    where: eq(notifications.employeeId, employeeId),
    orderBy: (t, { desc }) => [desc(t.createdAt)],
  });
}

export async function markRead(id: string, employeeId: string) {
  const n = await db.query.notifications.findFirst({
    where: and(eq(notifications.id, id), eq(notifications.employeeId, employeeId)),
  });
  if (!n) throw new AppError(404, 'Notification not found', 'NOT_FOUND');
  await db.update(notifications).set({ read: true }).where(eq(notifications.id, id));
  return { ...n, read: true };
}

export async function remove(id: string, employeeId: string) {
  const n = await db.query.notifications.findFirst({
    where: and(eq(notifications.id, id), eq(notifications.employeeId, employeeId)),
  });
  if (!n) throw new AppError(404, 'Notification not found', 'NOT_FOUND');
  await db.delete(notifications).where(eq(notifications.id, id));
}

export async function broadcast(data: {
  employeeIds: string[];
  title: string;
  message: string;
  type?: 'info' | 'warning' | 'success' | 'error';
}) {
  if (!data.employeeIds.length) return;
  await db.insert(notifications).values(
    data.employeeIds.map((eid) => ({
      employeeId: eid,
      title:      data.title,
      message:    data.message,
      type:       data.type ?? 'info',
    })),
  );
}
