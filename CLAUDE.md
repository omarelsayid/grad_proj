# SkillSync HRMS — Claude Context

## Project Overview
SkillSync is a skill-driven HRMS built as a graduation project. It consists of:

| Layer | Tech | Location | Port |
|---|---|---|---|
| Frontend | React 18 + Vite + Tailwind (Lovable UI) | `UI&UXLOVABLE/skillsynchrms-main/` | 5173 |
| Backend API | Node.js 20 + Express + TypeScript | `backend/` | 3000 |
| ML Service | Python 3.11 + FastAPI | `ml_service/` | 8000 |
| **HR Buddy** | **Python 3.11 + FastAPI RAG chatbot** | **`hr_buddy/backend/`** | **8001** |
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
`SkillSync_ML_Models.ipynb` — unified Colab-ready notebook with 4 models (33 cells).
Data lives in `Data/`. All fixes from `SkillSync_ML_Models_FIXED.ipynb` have been merged in.

### Model 1 — Turnover Prediction (Fixed 2026-04-12)
- **SMOTE leakage fix**: SMOTE now wrapped inside `ImbPipeline([("smote", SMOTE), ("clf", clf)])` — only fires on each CV fold's training split, not the full training set
- **Optuna tuning**: Replaces GridSearchCV; 50 Optuna trials per model for top 4 classifiers (Random Forest, XGBoost, LightGBM, Gradient Boosting)
- Saves: `best_turnover_model.pkl` (ImbPipeline), `scaler.pkl`, `turnover_features.pkl`

### Model 2 — Role Fit Scoring
- Removed `weighted_gap` leakage, R² ~0.92 (unchanged)

### Model 3 — Skill Gap Analysis (Fixed previously)
- `compute_realistic_gaps()` uses `pct_employees_meeting` as primary metric
- Criticality tiers: <10%=critical, <25%=high, <50%=medium, <75%=low, >=75%=surplus

### Model 4 — Training Recommendation / Learning Path (Fixed 2026-04-12)
- **LOO emp_avg_score fix**: Leave-one-out mean excludes current row's own score — prevents target leakage
- **employees_core.csv integration**: Optional extended features (age, tenure_years, kpi_score, etc.) when the file is present
- **GroupShuffleSplit**: Employee-group-aware train/test split prevents cross-employee data leakage
- **Optuna**: 50 trials for LightGBM hyperparameter tuning
- Saves: `learning_path_model.pkl`, `skill_chain_dag.pkl`, `learning_path_features.pkl`
- Fixed `employees_core.csv` employee ID format: `EMP0001` (not `EMP-0001`)

## ML Service Files (Updated 2026-04-12)
All service files updated to match the fixed notebook approach:

| File | Key Change |
|---|---|
| `training/train_turnover_model.py` | ImbPipeline + Optuna (replaces GridSearchCV + pre-SMOTE) |
| `training/train_learning_path_model.py` | LOO emp_avg_score, employees_core optional features, GroupShuffleSplit |
| `app/services/turnover_service.py` | `_top_factors()` unwraps ImbPipeline via `named_steps["clf"]` |
| `app/services/learning_path_service.py` | Loads `learning_path_features.pkl` for auto-alignment; zero-fills extra core columns |
| `app/services/skill_gaps_service.py` | `_get_criticality(pct_meeting)` with 5 tiers including "surplus" |
| `app/schemas/skill_gaps.py` | `criticality` comment updated to include "surplus" tier |

### Running Training Scripts
```bash
cd ml_service
python training/train_turnover_model.py    # → best_turnover_model.pkl, scaler.pkl, turnover_features.pkl
python training/train_learning_path_model.py  # → learning_path_model.pkl, skill_chain_dag.pkl, learning_path_features.pkl
```
Run from Colab: upload `SkillSync_ML_Models.ipynb` + all `Data/` files and run top-to-bottom.

## Flutter App (`skillsync_flutter/`)
Located at `skillsync_flutter/`. Flutter frontend with clean architecture, 3 portals (Employee, Manager, HR Admin), 50 mock employees, Riverpod state management, GoRouter navigation.

### Architecture
- **State management**: `flutter_riverpod` — providers in `presentation/*/dashboard/provider.dart`
- **Routing**: `go_router` — `ShellRoute` per portal, all routes in `lib/router.dart`
- **Theme**: `lib/core/theme/app_colors.dart` — primary, secondary, accent, warning, success, riskHigh, riskCritical, etc.
- **Mock data**: `lib/data/mock/` — 50 employees, roles, skills loaded via `FutureProvider`
- **Domain use cases**: `CalculateRoleFitUseCase`, `FindReplacementCandidatesUseCase`, `GetOrgSkillGapsUseCase`, `CalculateTurnoverRiskUseCase`

### Key Files
| File | Purpose |
|---|---|
| `lib/router.dart` | GoRouter with ShellRoute per portal + title maps |
| `lib/presentation/shell/app_shell.dart` | App shell with custom `_SidebarNav` (scrollable sidebar, no overflow) |
| `lib/presentation/shell/nav_item.dart` | Nav items for all 3 portals |
| `lib/core/widgets/stat_card.dart` | Compact horizontal stat card (row layout, `childAspectRatio: 2.4`) |

### Portals & Nav Items
- **Employee**: Dashboard, Skills, Learning, Mobility, Attendance, Leaves, Holidays, Payroll, Todos, Resignation, Notifications, Chat
- **Manager**: Dashboard, Team, Departments, Roles, Skills, Replacements, Attendance, Leaves, Payroll, Todos, Notifications, Chat
- **HR Admin**: Dashboard, Employees, Departments, Roles, Attendance, Leaves, Payroll, Resignations, Policies, Analytics, Turnover, Audit, Settings, Notifications, Chat

### Changes Made 2026-04-12
**Employee Dashboard** (`presentation/employee/dashboard/screen.dart`):
- Redesigned as `ConsumerStatefulWidget` with time-based greeting banner
- 4 compact stat cards: Role-Fit Score, Skills Mastered, Growth Potential, Learning Hours
- 2×2 Skill Profile grid with progress bars and category badges
- Skill Gap Analysis section with role dropdown (`_selectedRoleId` state)

**HR Dashboard** (`presentation/hr/dashboard/screen.dart`):
- Fixed `NoSuchMethodError: 'name' method not found` crash on `RiskLevel` enum
- Root cause: `.name` on Dart enums fails in Flutter web DDC; fixed with type-safe enum switch: `switch (r.riskLevel) { RiskLevel.critical => ..., ... }`
- Must type method params as `List<TurnoverRiskData>` (not bare `List`) for exhaustive switch to compile

**App Shell** (`presentation/shell/app_shell.dart`):
- Replaced `NavigationRail` with custom `_SidebarNav` using `ListView.builder` inside `Expanded`
- Fixes overflow crash when HR portal has 15+ nav items that exceed screen height
- `NavigationRail` has no built-in scroll — never use it for portals with many items

**StatCard** (`core/widgets/stat_card.dart`):
- Redesigned from tall vertical layout to compact horizontal row layout
- Uses `withValues(alpha: x)` — **never use deprecated `withOpacity()`** in this project

**Manager Portal** — New screens added:
- `presentation/manager/departments/screen.dart` — Department breakdown, avg tenure, member list
- `presentation/manager/roles/screen.dart` — Roles list with level badges, headcount, skill requirements
- Both wired in `router.dart` and `nav_item.dart`

### Important Flutter Notes
- Use `withValues(alpha: x)` not `withOpacity(x)` — deprecated API causes warnings
- Always type `List<ConcreteType>` for method params used in exhaustive switch expressions
- `NavigationRail` does not scroll — use `ListView.builder` inside `Expanded` for sidebars with many items
- Manager "team" is always `allEmps.take(10)` (mock — first 10 employees)

## HR Buddy (`hr_buddy/`)
RAG chatbot grounded in `SkillSync_Company_Policy_2026.pdf`. Answers policy questions with page citations. Added 2026-04-23.

### Stack
- **PDF parsing**: pypdf — page-aware chunking (700 chars, 150 overlap)
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (local, no API key) or HF Inference API
- **Vector store**: numpy `.npy` + `.json` (replaces ChromaDB — no C++ build tools needed on Windows)
- **LLM**: OpenAI-compatible client — configurable `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL`
- **Fallback mode**: if no LLM key configured, returns retrieved page text directly

### Structure
```
hr_buddy/backend/
  app/
    config.py              ← pydantic-settings, reads .env
    schemas.py             ← ChatRequest / ChatResponse / Citation / Health / Ingest
    main.py                ← FastAPI app, lifespan loads vector store on startup
    services/
      pdf_ingest.py        ← extract_chunks, _get_embedding_fn, save_store/load_store
      retriever.py         ← cosine_similarity over numpy matrix → RetrievedChunk list
      prompt_builder.py    ← SYSTEM_PROMPT + build_prompt() + build_fallback_answer()
      llm.py               ← chat_complete() using openai client
    data/store/            ← embeddings.npy + chunks.json (created after first ingest)
  tests/
    test_ingest.py         ← 6 unit tests for chunker/cleaner
    test_chat.py           ← integration tests for /chat /health /reset-index
  requirements.txt
  .env / .env.example
  Dockerfile
README.md                  ← full setup + curl examples
```

### API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Index readiness + chunk count |
| POST | `/ingest-pdf` | Load PDF → chunk → embed → persist |
| POST | `/chat` | RAG answer + page citations |
| DELETE | `/reset-index` | Wipe vector store |

### Start Commands
```bash
cd hr_buddy/backend
cp .env.example .env           # fill LLM_BASE_URL + LLM_API_KEY (optional)
py -m pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
curl -X POST http://localhost:8001/ingest-pdf    # one-time, ~30s first run
```

### Environment Variables (`.env`)
```
EMBEDDING_PROVIDER=local              # "local" | "hf_inference"
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_TOKEN=                             # only needed for hf_inference
LLM_BASE_URL=                         # e.g. https://api.openai.com/v1 or Groq
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
CHROMA_DIR=./app/data/store           # numpy store directory
PDF_PATH=../../SkillSync_Company_Policy_2026.pdf
TOP_K=5
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

### Flutter Integration
HR Buddy is wired into the Flutter app at:
- `lib/models/chat_models.dart` — `ChatMessage`, `ChatCitation`, `ChatResponse`
- `lib/services/hr_buddy_service.dart` — `isReady()`, `ingestPdf()`, `sendMessage()`
- `lib/widgets/chat_bubble.dart` — `ChatBubble` + `TypingIndicator` + citation chips
- `lib/presentation/hr_buddy/screen.dart` — full chat UI with welcome + suggestions
- `lib/presentation/shell/app_shell.dart` — `FloatingActionButton.extended` → opens HR Buddy in ALL portals

Backend URL is hardcoded to `http://localhost:8001` in `hr_buddy_service.dart` — change `_baseUrl` for deployment.

### HR Buddy Notes
- First run of `/ingest-pdf` downloads the sentence-transformers model (~90 MB) — subsequent runs are instant
- Without `LLM_BASE_URL`, fallback mode returns top retrieved chunk text directly (no LLM call)
- Re-ingesting is idempotent — it overwrites the previous `.npy` + `.json`
- PDF path is relative to `hr_buddy/backend/` — the default `../../SkillSync_Company_Policy_2026.pdf` points to the project root

## Important Notes
- Windows development environment (paths use forward slashes in code)
- No Redis required to start the API — BullMQ jobs are optional extensions
- `fetch` is used natively in Node 20+ for ML proxy (no axios needed)
- `employees_core.csv` employee IDs must be `EMP0001` format (no dash) for Model 4 join to work
- **Service ports**: React frontend=5173, Node.js API=3000, ML service=8000, HR Buddy=8001
