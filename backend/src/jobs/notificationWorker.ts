// src/jobs/notificationWorker.ts — BullMQ worker for broadcast notifications
import { Job } from 'bullmq';
import { createWorker } from './queue';
import { broadcast } from '../modules/notifications/service';
import { logger } from '../config/logger';

export interface NotificationJobData {
  employeeIds: string[];
  title:       string;
  message:     string;
  type?:       'info' | 'warning' | 'success' | 'error';
}

export const notificationWorker = createWorker(
  'notifications',
  async (job: Job<NotificationJobData>) => {
    const { employeeIds, title, message, type } = job.data;
    logger.info(`Sending notification to ${employeeIds.length} employees: ${title}`);
    await broadcast({ employeeIds, title, message, type });
    return { sent: employeeIds.length };
  },
  5,
);
