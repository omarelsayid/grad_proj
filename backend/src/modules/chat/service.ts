// src/modules/chat/service.ts
import { eq, or, and, desc } from 'drizzle-orm';
import { db } from '../../db';
import { chatMessages } from '../../db/schema';
import { env } from '../../config/env';

export async function getHistory(employeeId: string, limit = 50) {
  return db.query.chatMessages.findMany({
    where: (t, { or: o, eq: e }) => o(e(t.senderId, employeeId), e(t.receiverId, employeeId)),
    orderBy: (t, { asc }) => [asc(t.createdAt)],
    limit,
  });
}

export async function saveMessage(senderId: string, content: string, isAiResponse = false) {
  const id = crypto.randomUUID();
  await db.insert(chatMessages).values({ id, senderId, content, isAiResponse });
  return db.query.chatMessages.findFirst({ where: eq(chatMessages.id, id) });
}

export async function askAI(employeeId: string, question: string): Promise<string> {
  // Save user message
  await saveMessage(employeeId, question, false);

  // Forward to ML service (or fallback response)
  try {
    const response = await fetch(`${env.ML_SERVICE_URL}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ employee_id: employeeId, question }),
      signal:  AbortSignal.timeout(10000),
    });

    let answer = 'I am unable to process that right now.';
    if (response.ok) {
      const data = await response.json() as { answer?: string };
      answer = data.answer ?? answer;
    }

    // Save AI response
    await saveMessage(employeeId, answer, true);
    return answer;
  } catch {
    const fallback = 'Our AI assistant is temporarily unavailable. Please try again later.';
    await saveMessage(employeeId, fallback, true);
    return fallback;
  }
}
