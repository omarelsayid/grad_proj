// src/jobs/turnoverCacheWorker.ts — Nightly cron that recalculates turnover risk for all employees
import { createWorker, turnoverCacheQueue } from './queue';
import { calculateAllTurnoverRisks } from '../scoring/turnoverRisk';
import { db } from '../db';
import { turnoverRiskCache } from '../db/schema';
import { eq } from 'drizzle-orm';
import { logger } from '../config/logger';

export const turnoverCacheWorker = createWorker(
  'turnover-cache',
  async () => {
    logger.info('Starting nightly turnover risk recalculation...');
    const results = await calculateAllTurnoverRisks();

    for (const r of results) {
      // Upsert: delete old, insert new
      await db.delete(turnoverRiskCache).where(eq(turnoverRiskCache.employeeId, r.employeeId));
      await db.insert(turnoverRiskCache).values({
        employeeId:      r.employeeId,
        riskScore:       r.riskScore,
        riskLevel:       r.riskLevel,
        factorBreakdown: r.factorBreakdown,
        calculatedAt:    new Date(),
      });
    }

    logger.info(`Turnover risk cache updated for ${results.length} employees`);
    return { updated: results.length };
  },
  1,
);

/**
 * Schedule the nightly recalculation.
 * Call this from server.ts after startup.
 */
export async function scheduleTurnoverCron(): Promise<void> {
  if (!turnoverCacheQueue) return;
  // Run every day at 02:00
  await turnoverCacheQueue.add(
    'nightly-recalc',
    {},
    {
      repeat:        { pattern: '0 2 * * *' },
      removeOnComplete: { count: 5 },
      removeOnFail:     { count: 10 },
    },
  );
  logger.info('Nightly turnover risk cron scheduled (02:00)');
}
