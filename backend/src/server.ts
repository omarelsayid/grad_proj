// src/server.ts — Entry point: DB connection, Socket.io, BullMQ workers, HTTP listen
import { createServer } from 'http';
import { Server as SocketServer } from 'socket.io';
import app from './app';
import { connectDB, closeDB } from './db';
import { env } from './config/env';
import { logger } from './config/logger';
import { closeQueues } from './jobs/queue';

const httpServer = createServer(app);

// ── Socket.io — real-time notifications + chat ────────────────────────────────
const io = new SocketServer(httpServer, {
  cors: { origin: env.CORS_ORIGIN, methods: ['GET', 'POST'] },
});

io.on('connection', (socket) => {
  logger.debug(`Socket connected: ${socket.id}`);

  // Client sends { employeeId } to join their personal room
  socket.on('join', (employeeId: string) => {
    socket.join(`emp:${employeeId}`);
    logger.debug(`Socket ${socket.id} joined room emp:${employeeId}`);
  });

  socket.on('disconnect', () => {
    logger.debug(`Socket disconnected: ${socket.id}`);
  });
});

// Attach io to app so modules can emit events
app.set('io', io);

// ── Startup ───────────────────────────────────────────────────────────────────
async function start() {
  await connectDB();

  httpServer.listen(env.PORT, () => {
    logger.info(`🚀  SkillSync API running on http://localhost:${env.PORT}`);
    logger.info(`    Base URL: http://localhost:${env.PORT}/api/v1`);
    logger.info(`    Env:      ${env.NODE_ENV}`);
  });
}

// ── Graceful shutdown ─────────────────────────────────────────────────────────
async function shutdown(signal: string) {
  logger.info(`Received ${signal}. Shutting down gracefully...`);
  httpServer.close(async () => {
    await closeQueues();
    await closeDB();
    logger.info('Server closed');
    process.exit(0);
  });
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));
process.on('uncaughtException',  (err) => logger.error('Uncaught exception',  { error: err.message }));
process.on('unhandledRejection', (err) => logger.error('Unhandled rejection', { error: String(err) }));

start().catch((err) => {
  logger.error('Failed to start server', { error: (err as Error).message });
  process.exit(1);
});
