# SkillSync HRMS

> **A skill-driven Human Resource Management System** with AI-powered turnover prediction, replacement recommendations, and personalised learning paths — built as a Flutter Web application backed by a Node.js REST API and a Python ML service, all running locally against PostgreSQL.

<p align="center">
  <img src="https://img.shields.io/badge/Flutter_Web-3.19+-02569B?logo=flutter&logoColor=white" />
  <img src="https://img.shields.io/badge/Node.js-20+-339933?logo=node.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1 — Database Setup](#1--database-setup)
  - [2 — Node.js Backend](#2--nodejs-backend)
  - [3 — ML Models Service](#3--ml-models-service)
  - [4 — Flutter Web Frontend](#4--flutter-web-frontend)
- [Environment Variables](#environment-variables)
- [Authentication Flow](#authentication-flow)
- [ML Models](#ml-models)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [User Roles](#user-roles)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

SkillSync HRMS is a full-stack human resource management platform designed for skill-driven organisations. It runs entirely on your local machine — no cloud database or third-party auth providers required. It serves three user roles — **Employee**, **Manager**, and **HR Admin** — each with a dedicated web portal exposing relevant HR data, workflows, and AI-generated insights.

The system's intelligence layer provides:

- **Turnover Risk Prediction** — multi-factor ML scoring per employee
- **Replacement Candidate Ranking** — role-fit scoring across the workforce
- **Learning Path Recommendations** — personalised gap-closure suggestions
- **Org-Level Skill Gap Analysis** — demand vs. supply mapping across departments

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Flutter Web App  (browser)                   │
│   Employee Portal │ Manager Portal │ HR Admin Portal      │
│        Bloc/Cubit · Dio · Hive (IndexedDB) · fl_chart     │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTP / REST + JWT
                          │ (localhost:3000)
┌─────────────────────────▼────────────────────────────────┐
│                  Node.js Backend API                      │
│         Express · TypeScript · OAuth2 / JWT Auth          │
│   Attendance · Leave · Payroll · Notifications            │
│   Resignation · Audit Logs · Policy Management            │
└───────────────┬──────────────────┬────────────────────────┘
                │ HTTP             │ pg (node-postgres)
                │ (localhost:8000) │ (localhost:5432)
┌───────────────▼──────┐  ┌───────▼────────────────────────┐
│  Python ML Service   │  │     PostgreSQL 15 (local)       │
│  FastAPI             │  │  profiles · attendance          │
│  Turnover Risk       │  │  leave_requests · payroll       │
│  Role Fit Scoring    │  │  todos · notifications          │
│  Skill Gap Analysis  │  │  audit_logs · departments       │
│  Learning Paths      │  │  job_roles · holidays           │
└──────────────────────┘  └────────────────────────────────┘
```

---

## Tech Stack

### Frontend — Flutter Web

| Category | Technology |
|---|---|
| Framework | Flutter 3.19+ (Web target) |
| Language | Dart 3.3+ |
| State Management | Bloc (Cubit) |
| Networking | Dio |
| Local Storage | Hive (IndexedDB adapter for web) + SharedPreferences |
| Charts | fl_chart |
| Routing | Flutter Navigator 2.0 (`onGenerateRoute`) |
| Authentication | OAuth2 + JWT (Backend-driven) |
| Dependency Injection | `get_it` + `injectable` |

### Backend — Node.js

| Category | Technology |
|---|---|
| Runtime | Node.js 20+ |
| Framework | Express.js |
| Language | TypeScript |
| Database Driver | `node-postgres` (pg) |
| Query Builder | `kysely` |
| Authentication | OAuth2 + JWT (`jsonwebtoken`) |
| Validation | Zod |
| File Uploads | Multer |
| Background Jobs | BullMQ + Redis |
| Logging | Winston |
| Testing | Jest + Supertest |

### ML Models — Python

| Category | Technology |
|---|---|
| Runtime | Python 3.11+ |
| Framework | FastAPI |
| ML Libraries | scikit-learn, pandas, numpy |
| Database Driver | `psycopg2` |
| Model Serialisation | joblib |
| API Schema | Pydantic |
| Testing | pytest |

### Infrastructure

| Category | Technology |
|---|---|
| Database | PostgreSQL 15 (local) |
| Authentication | Custom OAuth2 + JWT (Node.js — no external provider) |
| In-app Notifications | REST polling (GET `/notifications`) |
| Object Storage | Local filesystem via Multer |
| CI/CD | GitHub Actions |

---

## Repository Structure

```
skillsync-hrms/
├── flutter_app/                    # Flutter Web application
│   ├── lib/
│   │   ├── core/
│   │   │   ├── di/                 # Dependency injection (get_it)
│   │   │   ├── network/            # Dio client, interceptors, base URL config
│   │   │   ├── router/             # onGenerateRoute, route name constants
│   │   │   ├── storage/            # Hive boxes, SharedPreferences helpers
│   │   │   ├── theme/              # App theme, colours, typography
│   │   │   └── utils/              # Date helpers, formatters, validators
│   │   ├── features/
│   │   │   ├── auth/               # Login, registration, JWT management
│   │   │   ├── employee/           # Employee portal — 12 sub-features
│   │   │   │   ├── dashboard/
│   │   │   │   ├── skills/
│   │   │   │   ├── learning/
│   │   │   │   ├── mobility/
│   │   │   │   ├── attendance/
│   │   │   │   ├── leaves/
│   │   │   │   ├── holidays/
│   │   │   │   ├── payroll/
│   │   │   │   ├── todos/
│   │   │   │   ├── resignation/
│   │   │   │   ├── notifications/
│   │   │   │   └── chat/
│   │   │   ├── manager/            # Manager portal — 10 sub-features
│   │   │   │   ├── dashboard/
│   │   │   │   ├── team/
│   │   │   │   ├── skills/
│   │   │   │   ├── replacements/
│   │   │   │   ├── attendance/
│   │   │   │   ├── leaves/
│   │   │   │   ├── payroll/
│   │   │   │   ├── todos/
│   │   │   │   ├── notifications/
│   │   │   │   └── chat/
│   │   │   └── hr_admin/           # HR Admin portal — 16 sub-features
│   │   │       ├── dashboard/
│   │   │       ├── employees/
│   │   │       ├── departments/
│   │   │       ├── roles/
│   │   │       ├── attendance/
│   │   │       ├── leaves/
│   │   │       ├── payroll/
│   │   │       ├── resignations/
│   │   │       ├── policies/
│   │   │       ├── analytics/
│   │   │       ├── audit/
│   │   │       ├── settings/
│   │   │       ├── notifications/
│   │   │       ├── chat/
│   │   │       └── turnover/
│   │   └── main.dart
│   ├── web/                        # Flutter Web entry point (index.html)
│   ├── test/
│   ├── pubspec.yaml
│   └── README.md
│
├── backend/                        # Node.js + Express API
│   ├── src/
│   │   ├── config/                 # Environment config, DB pool init
│   │   ├── db/
│   │   │   ├── migrations/         # Numbered SQL migration files
│   │   │   ├── seeds/              # Development seed data scripts
│   │   │   └── pool.ts             # node-postgres connection pool
│   │   ├── middleware/             # JWT auth guard, role check, error handler
│   │   ├── modules/
│   │   │   ├── auth/               # OAuth2 flow, JWT issue/refresh
│   │   │   ├── employees/
│   │   │   ├── attendance/
│   │   │   ├── leaves/
│   │   │   ├── payroll/
│   │   │   ├── todos/
│   │   │   ├── notifications/
│   │   │   ├── resignations/
│   │   │   ├── holidays/
│   │   │   ├── departments/
│   │   │   ├── roles/
│   │   │   ├── audit/
│   │   │   └── policies/
│   │   ├── jobs/                   # BullMQ background workers
│   │   └── app.ts
│   ├── test/
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
│
├── ml_service/                     # Python FastAPI ML service
│   ├── app/
│   │   ├── api/
│   │   │   ├── turnover.py         # POST /predict/turnover
│   │   │   ├── role_fit.py         # POST /predict/role-fit
│   │   │   ├── skill_gaps.py       # GET  /analysis/skill-gaps
│   │   │   └── learning_path.py    # POST /recommend/learning-path
│   │   ├── models/                 # Trained .joblib model files
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── db/                     # psycopg2 connection helpers
│   │   ├── services/               # Scoring logic, feature engineering
│   │   └── main.py
│   ├── training/                   # Training scripts and Jupyter notebooks
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
└── .github/
    └── workflows/
        ├── flutter_ci.yml
        ├── backend_ci.yml
        └── ml_service_ci.yml
```

---

## Features

### Employee Portal (12 Pages)

| Feature | Description |
|---|---|
| Dashboard | Welcome banner, quick stats, skill profile, skill gap summary, learning path preview, internal mobility matches |
| Skills | Personal skill cards with proficiency levels (0–5), skill chain visualisation showing career progression paths |
| Learning | Curated learning recommendations (courses, certifications, mentorships, projects) sorted by priority |
| Internal Mobility | Open roles ranked by the employee's current role-fit percentage |
| Attendance | Personal attendance records with status: present / absent / late / half-day / remote |
| Leaves | Leave balances (annual 21d, sick 10d, compassionate 5d) and request submission |
| Holidays | Egyptian public holiday calendar including company and optional holidays |
| Payroll | Payslip viewer with full salary breakdown |
| Todos | Personal task manager with priority levels and due dates |
| Resignation | Resignation submission form with notice period calculation |
| Notifications | In-app notification inbox (polled from the REST API) |
| AI Chat | HR Assistant chatbot powered by the backend LLM integration |

### Manager Portal (10 Pages)

| Feature | Description |
|---|---|
| Dashboard | Team overview, skill gap heatmap, replacement recommendations, team development summary |
| Team | Full team roster with roles, departments, and skill profiles |
| Team Skills | Aggregated skill distribution across the entire team |
| Replacements | Departure scenario selector → ranked replacement candidates with fit scores and skill gap breakdowns |
| Attendance | Team-wide attendance tracking |
| Leave Approval | Pending leave request review and approval workflow |
| Payroll | Team payroll overview |
| Todos | Manager task manager |
| Notifications | In-app inbox |
| AI Chat | HR Assistant |

### HR Admin Portal (16 Pages)

| Feature | Description |
|---|---|
| Dashboard | Org-wide stats, workforce analytics, skill gap chart, turnover risk card, policy quick-edit |
| Employee Directory | Searchable and filterable full employee directory |
| Add Employee | New employee onboarding form |
| Departments | Department creation and management |
| Role Definitions | Role editor with required skill minimum proficiency settings |
| Attendance | Organisation-wide attendance view |
| Leave Management | All leave requests across the organisation |
| Payroll | Org-wide payroll management |
| Resignations | Resignation tracking, approval, and offboarding workflow |
| Policy Editor | Inline editor for skill policies, role policies, and the L&D catalogue |
| Analytics | Workforce analytics with bar, pie, and area charts via fl_chart |
| Audit Log | Immutable audit trail viewer for all HR events |
| Settings | HR system configuration |
| Notifications | In-app inbox |
| AI Chat | HR Assistant |
| Turnover Prediction | Per-employee ML risk scores, risk-factor breakdown, department/risk-level filters, and visualised charts |

---

## Getting Started

### Prerequisites

| Tool | Version | Required For |
|---|---|---|
| Flutter SDK | 3.19+ | Web frontend |
| Dart SDK | 3.3+ | Web frontend |
| Node.js | 20+ | Backend API |
| npm | 10+ | Backend API |
| Python | 3.11+ | ML service |
| pip | 23+ | ML service |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Background job queues (BullMQ) |

Make sure `psql`, `node`, `python3`, and `flutter` are all on your `PATH` before proceeding.

---

### 1 — Database Setup

#### Create the local database and user

```bash
psql -U postgres
```

```sql
CREATE USER skillsync WITH PASSWORD 'skillsync_password';
CREATE DATABASE skillsync_db OWNER skillsync;
GRANT ALL PRIVILEGES ON DATABASE skillsync_db TO skillsync;
\q
```

#### Run migrations

```bash
cd backend

# Install dependencies first
npm install

# Apply all numbered migration files in order
npm run db:migrate
```

Migration files live in `src/db/migrations/` and create all 12 tables.

#### Seed development data

```bash
npm run db:seed
```

This loads 50 deterministic demo employees across departments, complete with attendance records, leave balances, skill profiles, and payroll data so every portal is immediately usable without manual data entry.

---

### 2 — Node.js Backend

#### Install dependencies

```bash
cd backend
npm install
```

#### Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in your local values:

```env
PORT=3000
NODE_ENV=development

# PostgreSQL (local)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skillsync_db
DB_USER=skillsync
DB_PASSWORD=skillsync_password

# JWT
JWT_SECRET=replace_with_a_long_random_string_min_32_chars
JWT_EXPIRES_IN=7d
REFRESH_TOKEN_SECRET=replace_with_another_long_random_string
REFRESH_TOKEN_EXPIRES_IN=30d

# ML Service (local)
ML_SERVICE_URL=http://localhost:8000

# Redis (local, for BullMQ)
REDIS_URL=redis://localhost:6379

# CORS — Flutter Web dev server
CORS_ORIGIN=http://localhost:4200

# File uploads
UPLOAD_DIR=./uploads
```

#### Start the server

```bash
# Development — hot reload via ts-node-dev
npm run dev

# Production build
npm run build
npm start
```

The API is available at `http://localhost:3000`.  
Interactive OpenAPI docs: `http://localhost:3000/api/v1/docs`

#### Run tests

```bash
npm test
npm run test:coverage
```

---

### 3 — ML Models Service

#### Create a virtual environment

```bash
cd ml_service
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

#### Install dependencies

```bash
pip install -r requirements.txt
```

#### Configure environment

```bash
cp .env.example .env
```

```env
# PostgreSQL (local — ML service reads employee data for training)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skillsync_db
DB_USER=skillsync
DB_PASSWORD=skillsync_password

MODEL_DIR=./app/models
LOG_LEVEL=INFO
```

#### Train or load pre-trained models

Pre-trained `.joblib` files for the seeded demo dataset are included in `app/models/` so you can run the service immediately without training. To retrain against your own data:

```bash
python training/train_turnover_model.py
python training/train_role_fit_model.py
```

#### Start the service

```bash
# Development — auto-reload
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Interactive API docs: `http://localhost:8000/docs`

#### Run tests

```bash
pytest
pytest --cov=app tests/
```

---

### 4 — Flutter Web Frontend

#### Install dependencies

```bash
cd flutter_app
flutter pub get
```

#### Configure environment

Create `flutter_app/.env` (loaded via `flutter_dotenv`):

```env
API_BASE_URL=http://localhost:3000/api/v1
```

#### Generate code (Hive adapters + injectable)

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

#### Enable Flutter Web (one-time setup)

```bash
flutter config --enable-web
```

#### Run in the browser

```bash
# Chrome — recommended for development
flutter run -d chrome

# Specify a port
flutter run -d chrome --web-port 4200

# List available devices
flutter devices
```

#### Build for production

```bash
flutter build web --release
```

Output lands in `flutter_app/build/web/`. Serve with any static file server:

```bash
cd flutter_app/build/web
python3 -m http.server 4200
# open http://localhost:4200
```

#### Run tests

```bash
flutter test
flutter test --coverage
```

---

## Environment Variables

### Complete Reference

| Variable | Service | Description | Required |
|---|---|---|---|
| `API_BASE_URL` | Flutter | Backend API base URL | ✅ |
| `PORT` | Backend | Express server port (default 3000) | ✅ |
| `DB_HOST` | Backend, ML | PostgreSQL host | ✅ |
| `DB_PORT` | Backend, ML | PostgreSQL port (default 5432) | ✅ |
| `DB_NAME` | Backend, ML | Database name | ✅ |
| `DB_USER` | Backend, ML | Database user | ✅ |
| `DB_PASSWORD` | Backend, ML | Database password | ✅ |
| `JWT_SECRET` | Backend | JWT signing secret (min 32 chars) | ✅ |
| `JWT_EXPIRES_IN` | Backend | Access token TTL (e.g. `7d`) | ✅ |
| `REFRESH_TOKEN_SECRET` | Backend | Refresh token signing secret | ✅ |
| `REFRESH_TOKEN_EXPIRES_IN` | Backend | Refresh token TTL (e.g. `30d`) | ✅ |
| `REDIS_URL` | Backend | Redis connection string | ✅ |
| `ML_SERVICE_URL` | Backend | Internal URL of the ML FastAPI service | ✅ |
| `CORS_ORIGIN` | Backend | Allowed origin for CORS (Flutter Web dev server) | ✅ |
| `UPLOAD_DIR` | Backend | Local path for uploaded files | ✅ |
| `MODEL_DIR` | ML | Path to trained `.joblib` model files | ✅ |
| `NODE_ENV` | Backend | `development` or `production` | ❌ |
| `LOG_LEVEL` | Backend, ML | Logging verbosity (`debug` / `info` / `warn` / `error`) | ❌ |

---

## Authentication Flow

SkillSync uses a fully self-contained **OAuth2 + JWT** flow implemented inside the Node.js backend. No external auth provider is involved.

```
Flutter Web App               Node.js Backend               PostgreSQL
      │                              │                           │
      │── POST /auth/login ─────────►│                           │
      │   { email, password }        │── SELECT user WHERE ─────►│
      │                              │   email = ?               │
      │                              │◄── { user, hashed_pw } ───│
      │                              │   bcrypt.compare()        │
      │                              │── SELECT role FROM ──────►│
      │                              │   user_roles              │
      │                              │◄── { role } ──────────────│
      │◄── { accessToken,  ─────────│                           │
      │      refreshToken,           │                           │
      │      user: { id, role } }    │                           │
      │                              │                           │
      │── Store tokens in Hive       │                           │
      │   (IndexedDB)                │                           │
      │── Navigate to role portal    │                           │
      │                              │                           │
      │── Subsequent requests ──────►│                           │
      │   Authorization: Bearer <jwt>│── Verify JWT signature    │
      │                              │── Decode role claim       │
      │                              │── Authorise route         │
      │◄── Protected resource ───────│                           │
      │                              │                           │
      │   (401 on expired token)     │                           │
      │── POST /auth/refresh ───────►│                           │
      │   { refreshToken }           │── Validate refresh token  │
      │◄── { accessToken } ─────────│                           │
      │── Retry original request ───►│                           │
```

**Token storage in Flutter Web:** Access tokens and refresh tokens are stored in Hive backed by IndexedDB in the browser. The Dio interceptor automatically attaches the `Authorization: Bearer` header and handles silent token refresh on 401 responses — no manual token management required in feature code.

**Roles:** `employee` | `manager` | `hr_admin` — stored in the `user_roles` PostgreSQL table and embedded as a claim in the JWT. The backend middleware validates the role on every protected route. Flutter reads the role from the decoded token on login and routes to the correct portal.

**CORS:** The backend allows requests from `http://localhost:4200` in development. Update `CORS_ORIGIN` in `.env` for staging or production deployments.

---

## ML Models

### 1. Turnover Risk Prediction

**Endpoint:** `POST /predict/turnover`

**Input features:**

| Feature | Type | Description |
|---|---|---|
| `employee_id` | string | Employee identifier |
| `commute_distance_km` | float | Commute distance in kilometres |
| `tenure_days` | int | Days since hire date |
| `role_fit_score` | float | Current role fit percentage (0–100) |
| `absence_rate` | float | Absence rate as a decimal (0–1) |
| `late_arrivals_30d` | int | Late check-ins in the last 30 days |
| `leave_requests_90d` | int | Leave requests submitted in the last 90 days |
| `satisfaction_score` | float | Survey satisfaction score (0–100) |
| `attendance_status` | string | `normal` \| `at_risk` \| `critical` |

**Output:**

```json
{
  "employee_id": "emp_001",
  "risk_score": 72.4,
  "risk_level": "high",
  "top_factors": ["commute_distance_km", "tenure_days", "absence_rate"]
}
```

**Risk buckets:** `low` (0–30) · `medium` (31–55) · `high` (56–75) · `critical` (76–100)

### 2. Role Fit Scoring

**Endpoint:** `POST /predict/role-fit`

Computes a readiness percentage by comparing an employee's actual skill proficiencies against a target role's minimum requirements per skill.

**Output:** integer 0–100 plus a per-skill breakdown showing matching skills, missing skills, and proficiency gaps.

### 3. Org-Level Skill Gap Analysis

**Endpoint:** `GET /analysis/skill-gaps`

Aggregates skill demand (role requirements × headcount) vs. skill supply (employee proficiency averages) and returns a demand/supply ratio per skill, sorted by criticality.

### 4. Learning Path Recommendation

**Endpoint:** `POST /recommend/learning-path`

Given an employee's missing skills for a target role, filters and ranks the L&D catalogue by skill relevance and item priority (high → medium → low).

---

## Database Schema

All 12 tables live in your local PostgreSQL 15 instance. Numbered migration files are in `backend/src/db/migrations/`.

```sql
-- Access control
user_roles           ( user_id, role )

-- Core employee data
profiles             ( user_id, full_name, email, department, position,
                       salary, phone, hire_date, avatar_url )

-- Attendance & time tracking
attendance           ( user_id, date, check_in, check_out, status, type )

-- Leave management
leave_requests       ( user_id, leave_type, start_date, end_date,
                       reason, status, approved_by )
leave_balances       ( user_id, leave_type, total_days, used_days, year )

-- Payroll
payroll              ( user_id, month, year, basic_salary, allowances,
                       deductions, net_salary, status, paid_date )

-- Productivity
todos                ( user_id, title, description, due_date,
                       priority, completed )

-- In-app notifications (polled by client)
notifications        ( user_id, title, message, type, read, created_at )

-- Offboarding
resignation_requests ( user_id, last_working_date, notice_period_days,
                       reason, status, approved_by )

-- Organisation structure
holidays             ( name, date, type, description )
departments          ( name, description, manager_id )
job_roles            ( title, department, description,
                       required_skills JSONB,
                       salary_range_min, salary_range_max )

-- Compliance
audit_logs           ( user_id, action, entity_type, entity_id,
                       old_values JSONB, new_values JSONB, ip_address )
```

---

## API Reference

The backend exposes a versioned REST API at `http://localhost:3000/api/v1`. Every endpoint except `/auth/*` requires `Authorization: Bearer <accessToken>` in the request header.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Email + password → access token + refresh token |
| POST | `/auth/register` | New user registration |
| POST | `/auth/refresh` | Exchange refresh token for a new access token |
| POST | `/auth/logout` | Invalidate the refresh token |

### Employees

| Method | Endpoint | Role Required |
|---|---|---|
| GET | `/employees` | manager, hr_admin |
| GET | `/employees/:id` | any (employees see own record only) |
| POST | `/employees` | hr_admin |
| PATCH | `/employees/:id` | hr_admin |
| DELETE | `/employees/:id` | hr_admin |

### Attendance

| Method | Endpoint | Role Required |
|---|---|---|
| GET | `/attendance` | any (scoped by role) |
| POST | `/attendance/check-in` | employee |
| POST | `/attendance/check-out` | employee |

### Leaves

| Method | Endpoint | Role Required |
|---|---|---|
| GET | `/leaves` | any (scoped by role) |
| POST | `/leaves` | employee |
| PATCH | `/leaves/:id/approve` | manager, hr_admin |
| PATCH | `/leaves/:id/reject` | manager, hr_admin |

### Notifications

| Method | Endpoint | Role Required |
|---|---|---|
| GET | `/notifications` | any (own inbox) |
| PATCH | `/notifications/:id/read` | any |
| DELETE | `/notifications/:id` | any |

### ML Predictions _(proxied from the ML service)_

| Method | Endpoint | Role Required |
|---|---|---|
| POST | `/ml/turnover` | hr_admin |
| POST | `/ml/role-fit` | manager, hr_admin |
| GET | `/ml/skill-gaps` | hr_admin |
| POST | `/ml/learning-path` | employee, manager, hr_admin |

Full interactive docs are at `http://localhost:3000/api/v1/docs` in development mode.

---

## User Roles

| Role | Access Scope | Portal Route |
|---|---|---|
| `employee` | Own profile, skills, learning, attendance, leaves, payroll, todos, resignation | `/employee/*` |
| `manager` | Employee-level access + team data, leave approvals, replacement recommendations | `/manager/*` |
| `hr_admin` | Full org access, policy management, analytics, turnover prediction, audit log | `/hr/*` |

Role is assigned at registration, stored in the `user_roles` table, embedded in the JWT claim, and read by Flutter on login to navigate the user to their portal. The backend enforces role checks on every protected route via middleware.

---

## Contributing

Contributions are welcome. Please follow the guidelines below to keep the codebase consistent across three languages.

### Branching Strategy

```
main          ← production-ready code only
develop       ← integration branch
feature/*     ← new features  (branched from develop)
fix/*         ← bug fixes     (branched from develop)
hotfix/*      ← urgent fixes  (branched from main)
```

### Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(flutter): add skill chain visualisation to employee dashboard
fix(backend): correct JWT expiry calculation for refresh tokens
feat(db): add index on attendance.user_id for query performance
chore(ml): update scikit-learn to 1.5.0
docs: update API reference for /ml/role-fit endpoint
```

### Pull Request Checklist

- [ ] All new code is covered by unit tests
- [ ] `flutter analyze` passes with no warnings
- [ ] `npm run lint` passes for backend changes
- [ ] `pytest` passes for ML service changes
- [ ] API changes are reflected in the OpenAPI spec
- [ ] New columns or tables include a numbered migration file
- [ ] `.env.example` is updated for any new environment variables

### Code Style

**Flutter/Dart:** `dart format .` is enforced in CI. Follow the [Dart style guide](https://dart.dev/guides/language/effective-dart/style).

**Node.js/TypeScript:** ESLint + Prettier configured in `backend/.eslintrc.json`. Run `npm run lint:fix` before committing.

**Python:** Black + isort + flake8 configured in `ml_service/pyproject.toml`. Run `black . && isort .` before committing.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](./LICENSE) for details.

---

<p align="center">Built with ❤️ for skill-driven HR teams</p>
