// src/db/index.ts — Drizzle + pg connection pool
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';
import { env } from '../config/env';
import { logger } from '../config/logger';

const pool = new Pool({
  connectionString: env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  ssl: env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

pool.on('error', (err) => {
  logger.error('Unexpected pg pool error', { error: err.message });
});

export const db = drizzle(pool, { schema, logger: env.NODE_ENV === 'development' });

export async function connectDB(): Promise<void> {
  const client = await pool.connect();
  client.release();
  logger.info('✅  PostgreSQL connected');
}

export async function closeDB(): Promise<void> {
  await pool.end();
  logger.info('PostgreSQL pool closed');
}
