// src/modules/todos/service.ts
import { eq, and } from 'drizzle-orm';
import { db } from '../../db';
import { todos } from '../../db/schema';
import { AppError } from '../../middleware/errorHandler';

export async function getAll(employeeId: string) {
  return db.query.todos.findMany({
    where: eq(todos.employeeId, employeeId),
    orderBy: (t, { desc }) => [desc(t.createdAt)],
  });
}

export async function create(employeeId: string, data: {
  title: string;
  description?: string;
  dueDate?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}) {
  const id = crypto.randomUUID();
  await db.insert(todos).values({ id, employeeId, title: data.title, description: data.description ?? '', dueDate: data.dueDate, priority: data.priority ?? 'medium' });
  return db.query.todos.findFirst({ where: eq(todos.id, id) });
}

export async function update(id: string, employeeId: string, data: Partial<{
  title: string; description: string; dueDate: string; priority: 'low' | 'medium' | 'high' | 'urgent'; completed: boolean;
}>) {
  const existing = await db.query.todos.findFirst({ where: and(eq(todos.id, id), eq(todos.employeeId, employeeId)) });
  if (!existing) throw new AppError(404, 'Todo not found', 'NOT_FOUND');
  await db.update(todos).set({ ...data, updatedAt: new Date() }).where(eq(todos.id, id));
  return db.query.todos.findFirst({ where: eq(todos.id, id) });
}

export async function remove(id: string, employeeId: string) {
  const existing = await db.query.todos.findFirst({ where: and(eq(todos.id, id), eq(todos.employeeId, employeeId)) });
  if (!existing) throw new AppError(404, 'Todo not found', 'NOT_FOUND');
  await db.delete(todos).where(eq(todos.id, id));
}
