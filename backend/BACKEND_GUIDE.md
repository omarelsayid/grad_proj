# SkillSync Backend — Complete Implementation Guide

## Architecture Overview

```
Flutter Web ──HTTP/REST──► Express API (port 3000)
                                    │
                    ┌───────────────┼───────────────────┐
                    │               │                   │
               PostgreSQL      ML Service          Redis/BullMQ
             (Supabase)       (port 8000)         (background jobs)
```

---

## 1 — Setup

### Install dependencies
```bash
cd backend
npm install
```

### Configure environment
```bash
cp .env.example .env
```

Edit `.env` — minimum required fields:
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
JWT_SECRET=at_least_32_random_characters_here_replace_me
REFRESH_TOKEN_SECRET=another_32_random_characters_different_from_above
```

### Push schema to Supabase (first time only)
```bash
npm run db:push
```

### Seed all data (50 employees, 28 skills, 22 roles, holidays)
```bash
npm run db:seed
```

### Start dev server
```bash
npm run dev
# → http://localhost:3000
```

---

## 2 — Database Schema (23 tables)

| Table | Purpose |
|---|---|
| `users` | Auth credentials (email + bcrypt hash) |
| `refresh_tokens` | JWT refresh token rotation |
| `user_roles` | One role per user (employee/manager/hr_admin) |
| `employees` | Employee profiles linked to users |
| `skills` | 28 skill definitions |
| `related_skills` | Skill adjacency (many-to-many) |
| `skill_chains` | Prerequisite chains (DAG) |
| `employee_skills` | Employee proficiency per skill (1-5) |
| `job_roles` | 22 role definitions |
| `role_required_skills` | Min proficiency per role/skill |
| `departments` | Department registry |
| `attendance` | Daily check-in/out records |
| `leave_balances` | Annual/sick/compassionate balances |
| `leave_requests` | Leave submissions + approval state |
| `payroll` | Monthly payslips |
| `todos` | Personal task manager |
| `notifications` | In-app inbox |
| `resignation_requests` | Resignation workflow |
| `holidays` | Egyptian public + company holidays |
| `audit_logs` | Immutable event trail |
| `learning_items` | L&D catalogue |
| `chat_messages` | AI HR chat history |
| `turnover_risk_cache` | Nightly-cached risk scores |

---

## 3 — API Reference

**Base URL:** `http://localhost:3000/api/v1`

All endpoints except `/auth/*` require:
```
Authorization: Bearer <accessToken>
```

### Auth
| Method | Endpoint | Body |
|---|---|---|
| POST | `/auth/register` | `{ email, password, name, role? }` |
| POST | `/auth/login` | `{ email, password }` |
| POST | `/auth/refresh` | `{ refreshToken }` |
| POST | `/auth/logout` | `{ refreshToken }` |

**Login response shape** (matches Flutter `AuthResult`):
```json
{
  "accessToken":  "eyJ...",
  "refreshToken": "eyJ...",
  "role":         "employee",
  "employee": {
    "id": "emp01", "name": "Ahmed Hassan", "email": "...",
    "currentRole": "Software Engineer", "roleId": "r02",
    "department": "Engineering", "joinDate": "2021-03-15",
    "salary": 18000, "commuteDistance": "moderate",
    "satisfactionScore": 72,
    "skills": [{ "skillId": "sk06", "proficiency": 4, "lastAssessed": "2024-01-01" }]
  }
}
```

### Employees
| Method | Endpoint | Roles |
|---|---|---|
| GET | `/employees` | employee (own), manager, hr_admin |
| GET | `/employees/me` | all |
| GET | `/employees/:id` | all (employee: own only) |
| POST | `/employees` | hr_admin |
| PATCH | `/employees/:id` | hr_admin |
| DELETE | `/employees/:id` | hr_admin |
| PUT | `/employees/:id/skills/:skillId` | employee (own), hr_admin |

### Skills & Roles
| Method | Endpoint | Roles |
|---|---|---|
| GET | `/skills` | all |
| GET | `/skills/chains` | all |
| GET | `/roles` | all |
| GET | `/roles/:id` | all |
| POST | `/skills` | hr_admin |
| POST | `/roles` | hr_admin |

### Attendance
| Method | Endpoint | Roles |
|---|---|---|
| GET | `/attendance` | all (scoped by role) |
| POST | `/attendance/check-in` | employee |
| POST | `/attendance/check-out` | employee |

### Leaves
| Method | Endpoint |
|---|---|
| GET | `/leaves` |
| GET | `/leaves/balances` |
| POST | `/leaves` |
| PATCH | `/leaves/:id/approve` |
| PATCH | `/leaves/:id/reject` |

### ML / Scoring (in-process, no ML service needed for these)
| Method | Endpoint | Roles |
|---|---|---|
| GET | `/ml/org-skill-gaps` | manager, hr_admin |
| POST | `/ml/replacements` | manager, hr_admin |
| POST | `/ml/turnover` | hr_admin |
| POST | `/ml/role-fit` | manager, hr_admin |
| GET | `/ml/skill-gaps` | hr_admin |
| POST | `/ml/learning-path` | all |

---

## 4 — Demo Credentials (after seed)

| Role | Email | Password |
|---|---|---|
| Employee | ahmed.hassan@skillsync.dev | Employee@123 |
| Manager | tarek.mansour@skillsync.dev | Manager@123 |
| HR Admin | rana.essam@skillsync.dev | Admin@123 |

---

## 5 — Flutter Integration Steps

### 5a. Run `flutter pub get`
The `http: ^1.2.1` package has been added to `pubspec.yaml`.

### 5b. Providers — wire ApiClient instead of mock repos

In `lib/presentation/auth/auth_provider.dart`, replace `MockEmployeeRepository` / `MockSkillRepository` with API-backed implementations. Pattern:

```dart
// lib/data/repositories/api_employee_repository.dart
import '../../services/api_client.dart';
import '../../domain/repositories/employee_repository.dart';

class ApiEmployeeRepository implements EmployeeRepository {
  final _api = ApiClient.instance;

  @override
  Future<List<Employee>> getAll() async {
    final rows = await _api.getEmployees();
    return rows.map((r) => _parse(r as Map<String, dynamic>)).toList();
  }
  // ... implement remaining interface methods
}
```

Then in `auth_provider.dart`:
```dart
final employeeRepositoryProvider = Provider<EmployeeRepository>(
  (_) => ApiEmployeeRepository(),   // ← replace MockEmployeeRepository
);
```

### 5c. Skills & roles — replace FutureProvider

In `lib/presentation/employee/dashboard/provider.dart`:
```dart
final employeeSkillsProvider = FutureProvider<List<Skill>>((ref) async {
  final raw = await ApiClient.instance.getSkills();
  return raw.map((r) => Skill.fromJson(r as Map<String, dynamic>)).toList();
});

final employeeRolesProvider = FutureProvider<List<Role>>((ref) async {
  final raw = await ApiClient.instance.getRoles();
  return raw.map((r) => Role.fromJson(r as Map<String, dynamic>)).toList();
});
```

### 5d. What to keep vs replace

| File | Action |
|---|---|
| `lib/data/mock/mock_employees.dart` | **Remove** (use `/employees` API) |
| `lib/data/mock/mock_skills.dart` | **Remove** (use `/skills` API) |
| `lib/data/mock/mock_roles.dart` | **Remove** (use `/roles` API) |
| `lib/data/mock/mock_attendance.dart` | **Remove** (use `/attendance` API) |
| `lib/data/repositories/mock_employee_repository.dart` | **Replace** with `ApiEmployeeRepository` |
| `lib/data/repositories/mock_skill_repository.dart` | **Replace** with `ApiSkillRepository` |
| `lib/domain/usecases/calculate_role_fit_use_case.dart` | **Keep** — used client-side for instant UI |
| `lib/domain/usecases/calculate_turnover_risk_use_case.dart` | **Keep** — used client-side for HR dashboard |
| `lib/domain/usecases/get_org_skill_gaps_use_case.dart` | **Keep** — keep for offline; or call `/ml/org-skill-gaps` |
| `lib/services/api_client.dart` | **New** — HTTP wrapper |
| `lib/services/auth_service.dart` | **New** — auth + JSON → entity parsing |

---

## 6 — Scoring Algorithms

All four algorithms live in `src/scoring/` and exactly mirror the Flutter use cases:

| Algorithm | File | Mirrors Flutter class |
|---|---|---|
| Role Fit | `roleFit.ts` | `CalculateRoleFitUseCase` |
| Turnover Risk | `turnoverRisk.ts` | `CalculateTurnoverRiskUseCase` |
| Replacement Candidates | `replacementCandidates.ts` | `FindReplacementCandidatesUseCase` |
| Org Skill Gaps | `skillGaps.ts` | `GetOrgSkillGapsUseCase` |

---

## 7 — Background Jobs (BullMQ)

Redis is **optional** — the API starts normally without it. Workers log a warning if Redis is unavailable.

| Queue | Trigger | What it does |
|---|---|---|
| `payroll` | Manual via `POST /payroll/generate` | Generates payslips for all employees |
| `notifications` | Service calls | Bulk notification delivery |
| `turnover-cache` | Nightly cron 02:00 | Recalculates risk for all 50 employees, caches result |

---

## 8 — Security

- **Helmet** — sets 11 security HTTP headers
- **CORS** — scoped to `CORS_ORIGIN` env var
- **Rate limiting** — 200 req / 15 min per IP
- **JWT** — HS256, 15-minute access + 30-day refresh with rotation
- **bcrypt** — cost factor 12 for password hashing
- **Audit log** — every mutating operation recorded automatically via `auditLog()` middleware
- **Role guard** — `authorize(...roles)` on every protected route

---

## 9 — Production Deployment

### Recommended: Railway (simplest for this stack)
```bash
railway login
railway init
railway add postgresql   # provisions Supabase-compatible PG
railway add redis        # for BullMQ
railway up
```
Set env vars in Railway dashboard. `npm start` runs `node dist/server.js`.

### Build for production
```bash
npm run build   # compiles TypeScript → dist/
npm start       # runs compiled JS
```

---

## 10 — Implementation Checklist (7 phases)

### Phase 1 — Foundation (Day 1)
- [x] Clone repo, `cd backend`
- [x] `cp .env.example .env` → fill DATABASE_URL + secrets
- [x] `npm install`
- [x] `npm run db:push` — push schema to Supabase
- [x] `npm run db:seed` — load 50 employees, skills, roles
- [x] `npm run dev` → confirm `/health` returns `{ status: "ok" }`

### Phase 2 — Auth verification (Day 1)
- [ ] POST `/auth/login` with demo credentials → get tokens
- [ ] GET `/employees/me` with Bearer token → employee profile
- [ ] POST `/auth/refresh` → new access token
- [ ] POST `/auth/logout` → 204

### Phase 3 — Flutter wiring (Day 2)
- [ ] `flutter pub get` (picks up `http` package)
- [ ] Login form now calls `AuthService.login()` → real JWT
- [ ] Replace `MockEmployeeRepository` → `ApiEmployeeRepository`
- [ ] Replace `MockSkillRepository` → `ApiSkillRepository`
- [ ] Delete mock data files

### Phase 4 — Feature screens (Day 3)
- [ ] Attendance — check-in/out buttons call real API
- [ ] Leaves — submit form, see balance from API
- [ ] Todos — full CRUD wired
- [ ] Notifications — polling from `/notifications`
- [ ] Chat — questions sent to `/chat/ask`

### Phase 5 — Manager & HR screens (Day 4)
- [ ] Replacement candidates — `/ml/replacements`
- [ ] Org skill gaps — `/ml/org-skill-gaps`
- [ ] Turnover risk — `/ml/turnover` or cached scores
- [ ] Leave approvals — PATCH `/leaves/:id/approve`
- [ ] Audit log — `/audit`

### Phase 6 — Background jobs (Day 5)
- [ ] Install + start Redis locally
- [ ] Trigger payroll generation job
- [ ] Verify nightly turnover cache cron registered
- [ ] Test notification broadcast

### Phase 7 — Production readiness (Day 6-7)
- [ ] `npm run build` passes with 0 errors
- [ ] Set production env vars
- [ ] Deploy to Railway / Render
- [ ] Point Flutter CORS_ORIGIN to production URL
- [ ] Smoke-test all three portals end-to-end
