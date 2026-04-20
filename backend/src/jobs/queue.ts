// src/jobs/queue.ts — BullMQ queue setup (Redis optional)
import { Queue, Worker } from 'bullmq';
import IORedis from 'ioredis';
import { env } from '../config/env';
import { logger } from '../config/logger';

let connection: IORedis | null = null;

function getConnection(): IORedis {
  if (!connection) {
    connection = new IORedis(env.REDIS_URL, {
      maxRetriesPerRequest: null,
      lazyConnect: true,
      enableOfflineQueue: false,
      retryStrategy: () => null, // don't retry — Redis is optional
    });
    connection.on('error', () => {}); // silence connection errors
  }
  return connection;
}

export function createQueue(name: string): Queue | null {
  try {
    return new Queue(name, { connection: getConnection() });
  } catch {
    logger.warn(`Could not create queue '${name}' — Redis may be unavailable`);
    return null;
  }
}

export function createWorker(
  name: string,
  processor: Parameters<typeof Worker>[1],
  concurrency = 1,
): Worker | null {
  try {
    const worker = new Worker(name, processor, { connection: getConnection(), concurrency });
    worker.on('completed', (job) => logger.debug(`[${name}] Job ${job.id} completed`));
    worker.on('failed',    (job, err) => logger.error(`[${name}] Job ${job?.id} failed`, { error: err.message }));
    return worker;
  } catch {
    logger.warn(`Could not create worker '${name}' — Redis may be unavailable`);
    return null;
  }
}

// Named queues
export const payrollQueue      = createQueue('payroll');
export const notificationQueue = createQueue('notifications');
export const turnoverCacheQueue = createQueue('turnover-cache');

export async function closeQueues(): Promise<void> {
  await payrollQueue?.close();
  await notificationQueue?.close();
  await turnoverCacheQueue?.close();
  await connection?.quit();
}
