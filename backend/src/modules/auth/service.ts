// src/modules/auth/service.ts
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { eq } from 'drizzle-orm';
import { db } from '../../db';
import { users, userRoles, employees, employeeSkills, refreshTokens } from '../../db/schema';
import { env } from '../../config/env';
import { AppError } from '../../middleware/errorHandler';
import type { JwtPayload } from '../../middleware/auth';

// ── Token helpers ──────────────────────────────────────────────────────────────
function signAccess(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: env.JWT_EXPIRES_IN } as jwt.SignOptions);
}

function signRefresh(userId: string): string {
  return jwt.sign({ sub: userId }, env.REFRESH_TOKEN_SECRET, {
    expiresIn: env.REFRESH_TOKEN_EXPIRES_IN,
  } as jwt.SignOptions);
}

function refreshExpiry(): Date {
  // parse "30d" → days → ms
  const match = /^(\d+)d$/.exec(env.REFRESH_TOKEN_EXPIRES_IN);
  const days  = match ? parseInt(match[1]!, 10) : 30;
  return new Date(Date.now() + days * 86400_000);
}

// ── buildUserResponse — shape returned to Flutter ─────────────────────────────
async function buildTokenResponse(userId: string, role: 'employee' | 'manager' | 'hr_admin', employeeId: string | null) {
  const accessToken  = signAccess({ sub: userId, email: '', role, employeeId });
  const refreshToken = signRefresh(userId);

  await db.insert(refreshTokens).values({
    userId,
    token:     refreshToken,
    expiresAt: refreshExpiry(),
  });

  // Fetch employee profile + skills if exists
  let employee = null;
  if (employeeId) {
    const rows = await db
      .select()
      .from(employees)
      .where(eq(employees.id, employeeId))
      .limit(1);
    const emp = rows[0] ?? null;
    if (emp) {
      const skillRows = await db
        .select()
        .from(employeeSkills)
        .where(eq(employeeSkills.employeeId, employeeId));
      employee = {
        ...emp,
        skills: skillRows.map((s) => ({
          skillId:     s.skillId,
          proficiency: s.proficiency,
          lastAssessed: s.lastAssessed,
        })),
      };
    }
  }

  return { accessToken, refreshToken, employee, role };
}

// ── register ──────────────────────────────────────────────────────────────────
export async function register(
  email: string,
  password: string,
  name: string,
  role: 'employee' | 'manager' | 'hr_admin' = 'employee',
) {
  const existing = await db.select({ id: users.id })
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);

  if (existing.length > 0) {
    throw new AppError(409, 'Email already registered', 'EMAIL_EXISTS');
  }

  const passwordHash = await bcrypt.hash(password, 12);
  const userId       = crypto.randomUUID();

  await db.insert(users).values({ id: userId, email: email.toLowerCase(), passwordHash });
  await db.insert(userRoles).values({ userId, role });

  // Try to link to existing employee by email
  const empRow = await db.select({ id: employees.id })
    .from(employees)
    .where(eq(employees.email, email.toLowerCase()))
    .limit(1);

  const employeeId = empRow[0]?.id ?? null;
  if (employeeId) {
    await db.update(employees).set({ userId }).where(eq(employees.id, employeeId));
  }

  return buildTokenResponse(userId, role, employeeId);
}

// ── login ─────────────────────────────────────────────────────────────────────
export async function login(email: string, password: string) {
  const rows = await db
    .select({
      id:           users.id,
      email:        users.email,
      passwordHash: users.passwordHash,
    })
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);

  const user = rows[0];
  if (!user) throw new AppError(401, 'Invalid credentials', 'INVALID_CREDENTIALS');

  const match = await bcrypt.compare(password, user.passwordHash);
  if (!match) throw new AppError(401, 'Invalid credentials', 'INVALID_CREDENTIALS');

  const roleRow = await db.select().from(userRoles).where(eq(userRoles.userId, user.id)).limit(1);
  const role = roleRow[0]?.role ?? 'employee';

  const empRow = await db.select({ id: employees.id })
    .from(employees)
    .where(eq(employees.email, user.email))
    .limit(1);
  const employeeId = empRow[0]?.id ?? null;

  return buildTokenResponse(user.id, role, employeeId);
}

// ── refresh ───────────────────────────────────────────────────────────────────
export async function refresh(token: string) {
  let payload: { sub: string };
  try {
    payload = jwt.verify(token, env.REFRESH_TOKEN_SECRET) as { sub: string };
  } catch {
    throw new AppError(401, 'Invalid refresh token', 'TOKEN_INVALID');
  }

  const row = await db.select()
    .from(refreshTokens)
    .where(eq(refreshTokens.token, token))
    .limit(1);

  if (!row[0] || row[0].expiresAt < new Date()) {
    throw new AppError(401, 'Refresh token expired or not found', 'TOKEN_EXPIRED');
  }

  // Rotate: delete old, issue new
  await db.delete(refreshTokens).where(eq(refreshTokens.token, token));

  const roleRow = await db.select().from(userRoles).where(eq(userRoles.userId, payload.sub)).limit(1);
  const role    = roleRow[0]?.role ?? 'employee';

  const empRow = await db.select({ id: employees.id, email: employees.email })
    .from(employees)
    .where(eq(employees.userId, payload.sub))
    .limit(1);
  const employeeId = empRow[0]?.id ?? null;

  return buildTokenResponse(payload.sub, role, employeeId);
}

// ── logout ────────────────────────────────────────────────────────────────────
export async function logout(token: string) {
  await db.delete(refreshTokens).where(eq(refreshTokens.token, token));
}
