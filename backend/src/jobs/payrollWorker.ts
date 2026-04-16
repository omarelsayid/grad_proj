// src/jobs/payrollWorker.ts — BullMQ worker for payroll generation
import { Job } from 'bullmq';
import { createWorker } from './queue';
import { generateMonthly } from '../modules/payroll/service';
import { logger } from '../config/logger';

export interface PayrollJobData {
  month: number;
  year:  number;
}

export const payrollWorker = createWorker(
  'payroll',
  async (job: Job<PayrollJobData>) => {
    const { month, year } = job.data;
    logger.info(`Processing payroll for ${year}-${month.toString().padStart(2, '0')}`);
    const records = await generateMonthly(month, year);
    logger.info(`Generated ${records.length} payroll records`);
    return { count: records.length };
  },
  3,
);
