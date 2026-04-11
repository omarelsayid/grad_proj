# SkillSync HRMS — Claude Context

## Project Overview
SkillSync is a skill-driven HRMS built as a graduation project. It consists of:

| Layer | Tech | Location | Port |
|---|---|---|---|
| Frontend | React 18 + Vite + Tailwind (Lovable UI) | `UI&UXLOVABLE/skillsynchrms-main/` | 5173 |
| Backend API | Node.js 20 + Express + TypeScript | `backend/` | 3000 |
| ML Service | Python 3.11 + FastAPI | `ml_service/` | 8000 |
| Database | PostgreSQL 15 | local | 5432 |

## Backend Structure (`backend/`)

```
backend/
├── src/
│   ├── config/
│   │   ├── env.ts          ← Zod env validation (reads .env)
│   │   └── logger.ts       ← Winston logger
│   ├── db/
│   │   ├── pool.ts         ← pg Pool + query/queryOne helpers
│   │   ├── migrate.ts      ← npm run db:migrate
│   │   ├── migrations/
│   │   │   └── 001_initial_schema.sql
│   │   └── seeds/
│   │       └── index.ts    ← npm run db:seed (3 demo accounts)
│   ├── middleware/
│   │   ├── auth.ts         ← JWT Bearer extraction → req.user
│   │   ├── roleCheck.ts    ← requireRole(...roles) guard
│   │   ├── errorHandler.ts ← Global error handler + AppError class
│   │   ├── validateBody.ts ← validateBody(zodSchema) middleware
│   │   └── auditLog.ts     ← auditLog({ action, entityType })
│   ├── modules/
│   │   ├── auth/           ← POST /auth/{login,register,refresh,logout}
│   │   ├── employees/      ← GET/POST/PATCH/DELETE /employees
│   │   ├── attendance/     ← GET /attendance, POST /check-in, /check-out
│   │   ├── leaves/         ← GET /leaves, POST, PATCH /:id/approve, GET /balances
│   │   ├── payroll/        ← GET/POST/PATCH /payroll
│   │   ├── todos/          ← Full CRUD /todos
│   │   ├── notifications/  ← GET /notifications, POST, PATCH /:id/read, DELETE
│   │   ├── resignations/   ← GET/POST/PATCH /resignations
│   │   ├── holidays/       ← GET/POST/DELETE /holidays
│   │   ├── departments/    ← Full CRUD /departments
│   │   ├── roles/          ← Full CRUD /roles (job roles)
│   │   ├── audit/          ← GET /audit (hr_admin only)
│   │   └── ml/             ← ML proxy: /ml/{turnover,role-fit,skill-gaps,learning-path}
│   ├── app.ts              ← Express app setup, routes mounted at /api/v1
│   └── server.ts           ← Entry point, DB connect, listen
├── test/
│   └── auth.test.ts
├── package.json
├── tsconfig.json
├── jest.config.ts
├── .eslintrc.json
└── .env.example
```

## API Base URL
All routes: `http://localhost:3000/api/v1/`

## Auth Flow
- Register → `POST /auth/register` → `{ user, tokens: { accessToken, refreshToken } }`
- Login    → `POST /auth/login`    → same shape
- Refresh  → `POST /auth/refresh`  → `{ accessToken }`
- Logout   → `POST /auth/logout`   → 204

Every protected endpoint requires `Authorization: Bearer <accessToken>`.

## Roles
| Role | Value |
|---|---|
| Employee | `employee` |
| Manager | `manager` |
| HR Admin | `hr_admin` |

Stored in `user_roles` table, embedded in JWT claim `role`.

## Database Schema (key tables)
- `users` — email + bcrypt password (replaces Supabase auth)
- `refresh_tokens` — token rotation
- `user_roles` — role assignment
- `profiles` — employee profile (links to users.id)
- `departments`, `job_roles`
- `attendance`, `leave_balances`, `leave_requests`
- `payroll`, `todos`, `notifications`
- `resignation_requests`, `holidays`, `audit_logs`

## Demo Credentials (after `npm run db:seed`)
| Role | Email | Password |
|---|---|---|
| HR Admin | admin@skillsync.dev | Admin@123 |
| Manager | manager@skillsync.dev | Manager@123 |
| Employee | emp@skillsync.dev | Employee@123 |

## Setup Commands
```bash
cd backend
cp .env.example .env     # fill in DB_NAME, DB_USER, etc.
npm install
npm run db:migrate       # create all tables
npm run db:seed          # insert demo data
npm run dev              # start with hot-reload on :3000
```

## Frontend (Lovable React App)
Located at `UI&UXLOVABLE/skillsynchrms-main/`.
- Currently wired to **Supabase** (see `src/integrations/supabase/client.ts`)
- **Next step**: replace Supabase calls with axios/fetch calls to `http://localhost:3000/api/v1`
- Routing is React Router v6 with portals: `/employee/*`, `/manager/*`, `/hr/*`
- Uses shadcn/ui + Tailwind + Recharts

## ML Service
Located at `ml_service/`. FastAPI at port 8000.
- `POST /predict/turnover`
- `POST /predict/role-fit`
- `GET  /analysis/skill-gaps`
- `POST /recommend/learning-path`

The Node.js backend proxies all ML calls via `/api/v1/ml/*`.

## ML Models (Notebook)
`SkillSync_ML_Models.ipynb` — full Colab-ready notebook with 4 models.
Data lives in `Data/`. Key fixes applied:
- Model 2 (Role Fit): removed `weighted_gap` leakage, R² ~0.92
- Model 4 (Learning Path): fixed join via `learning_resources.target_skill_id`, RMSE ~6.2

## Important Notes
- Windows development environment (paths use forward slashes in code)
- No Redis required to start the API — BullMQ jobs are optional extensions
- `fetch` is used natively in Node 20+ for ML proxy (no axios needed)
