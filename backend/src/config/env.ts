// src/config/env.ts — Zod-validated environment variables
import { z } from 'zod';
import { config } from 'dotenv';

config();

const envSchema = z.object({
  PORT:                     z.coerce.number().default(3000),
  NODE_ENV:                 z.enum(['development', 'production', 'test']).default('development'),
  DATABASE_URL:             z.string().min(1),
  JWT_SECRET:               z.string().min(32),
  JWT_EXPIRES_IN:           z.string().default('15m'),
  REFRESH_TOKEN_SECRET:     z.string().min(32),
  REFRESH_TOKEN_EXPIRES_IN: z.string().default('30d'),
  ML_SERVICE_URL:           z.string().url().default('http://localhost:8000'),
  REDIS_URL:                z.string().default('redis://localhost:6379'),
  CORS_ORIGIN:              z.string().default('http://localhost:4200'),
  RATE_LIMIT_WINDOW_MS:     z.coerce.number().default(900000),
  RATE_LIMIT_MAX:           z.coerce.number().default(200),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('❌  Invalid environment variables:\n', parsed.error.format());
  process.exit(1);
}

export const env = parsed.data;
