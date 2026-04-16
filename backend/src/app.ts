// src/app.ts — Express app wiring
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { env } from './config/env';
import { notFound, errorHandler } from './middleware/errorHandler';
import { logger } from './config/logger';

// Route imports
import authRouter         from './modules/auth/router';
import employeesRouter    from './modules/employees/router';
import skillsRouter       from './modules/skills/router';
import rolesRouter        from './modules/roles/router';
import attendanceRouter   from './modules/attendance/router';
import leavesRouter       from './modules/leaves/router';
import payrollRouter      from './modules/payroll/router';
import todosRouter        from './modules/todos/router';
import notificationsRouter from './modules/notifications/router';
import chatRouter         from './modules/chat/router';
import resignationsRouter from './modules/resignations/router';
import holidaysRouter     from './modules/holidays/router';
import departmentsRouter  from './modules/departments/router';
import auditRouter        from './modules/audit/router';
import mlRouter           from './modules/ml/router';

const app = express();

// ── Security middleware ────────────────────────────────────────────────────────
app.use(helmet());

app.use(cors({
  origin:      env.CORS_ORIGIN,
  methods:     ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
}));

app.use(rateLimit({
  windowMs:         env.RATE_LIMIT_WINDOW_MS,
  max:              env.RATE_LIMIT_MAX,
  standardHeaders:  true,
  legacyHeaders:    false,
  message:          { error: 'Too many requests, please try again later.' },
}));

// ── Body parsing ──────────────────────────────────────────────────────────────
app.use(express.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: true }));

// ── Request logging ───────────────────────────────────────────────────────────
app.use((req, _res, next) => {
  logger.debug(`${req.method} ${req.path}`);
  next();
});

// ── Health check ──────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString(), version: '1.0.0' });
});

// ── API v1 routes ─────────────────────────────────────────────────────────────
const v1 = '/api/v1';

app.use(`${v1}/auth`,          authRouter);
app.use(`${v1}/employees`,     employeesRouter);
app.use(`${v1}/skills`,        skillsRouter);
app.use(`${v1}/roles`,         rolesRouter);
app.use(`${v1}/attendance`,    attendanceRouter);
app.use(`${v1}/leaves`,        leavesRouter);
app.use(`${v1}/payroll`,       payrollRouter);
app.use(`${v1}/todos`,         todosRouter);
app.use(`${v1}/notifications`, notificationsRouter);
app.use(`${v1}/chat`,          chatRouter);
app.use(`${v1}/resignations`,  resignationsRouter);
app.use(`${v1}/holidays`,      holidaysRouter);
app.use(`${v1}/departments`,   departmentsRouter);
app.use(`${v1}/audit`,         auditRouter);
app.use(`${v1}/ml`,            mlRouter);

// ── Error handling ────────────────────────────────────────────────────────────
app.use(notFound);
app.use(errorHandler);

export default app;
