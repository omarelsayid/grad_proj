# `CLAUDE.md` — SkillSync HRMS Developer & AI Assistant Guide

##  Project Identity

**SkillSync HRMS** is a **skill-driven Human Resource Management System** built as a **multi-service full-stack platform** combining:

* Flutter Web frontend
* Node.js REST API backend
* Python FastAPI ML service
* PostgreSQL database (local-first architecture)

This project is designed to operate **entirely locally**, with no dependency on external cloud services for authentication or data storage.

---

##  System Purpose

The system enables organizations to:

* Monitor and manage employee lifecycle data
* Predict employee turnover using ML models
* Recommend internal replacements based on skill fit
* Identify organizational skill gaps
* Generate personalized learning paths

It supports three primary roles:

* **Employee**
* **Manager**
* **HR Admin**

---

## System Architecture Overview

The system is composed of three tightly integrated layers:

### 1. Frontend — Flutter Web

* Multi-portal UI (Employee / Manager / HR Admin)
* Uses **Bloc/Cubit** for state management
* Communicates with backend via **REST + JWT**
* Stores tokens in **Hive (IndexedDB)**

### 2. Backend — Node.js (Express + TypeScript)

* Central API gateway
* Handles:

  * Authentication (OAuth2 + JWT)
  * Business logic (HR operations)
  * Role-based access control
* Connects to:

  * PostgreSQL (primary data store)
  * Redis (background jobs via BullMQ)
  * Python ML service

### 3. ML Service — Python (FastAPI)

* Provides intelligent features:

  * Turnover prediction
  * Role-fit scoring
  * Skill gap analysis
  * Learning recommendations
* Uses:

  * scikit-learn models
  * pandas / numpy for feature processing

---

##  Core Data Flow

### Authentication Flow

1. User logs in via Flutter UI
2. Backend validates credentials from PostgreSQL
3. JWT + refresh token issued
4. Tokens stored in Hive
5. All future requests include `Authorization: Bearer <token>`

### ML Integration Flow

1. Frontend triggers ML-related request
2. Node.js backend proxies request to FastAPI service
3. ML service processes data and returns predictions
4. Backend forwards response to frontend

---

##  Key Backend Modules

Located under: `backend/src/modules/`

* `auth` — login, JWT, refresh flow
* `employees` — employee CRUD
* `attendance` — check-in/out tracking
* `leaves` — leave requests & approvals
* `payroll` — salary and payslip handling
* `notifications` — in-app messaging
* `resignations` — offboarding workflow
* `departments` / `roles` — org structure
* `audit` — system activity logging
* `policies` — HR policy management

---

##  ML Capabilities

### 1. Turnover Prediction

* Predicts employee risk score (0–100)
* Outputs:

  * risk level (low → critical)
  * contributing factors

### 2. Role Fit Scoring

* Compares employee skills vs role requirements
* Returns:

  * fit percentage
  * skill gap breakdown

### 3. Skill Gap Analysis

* Aggregates org-wide:

  * skill demand vs supply
* Outputs prioritized gaps

### 4. Learning Path Recommendation

* Suggests:

  * courses
  * certifications
  * projects
    based on missing skills

---

## Database Overview (PostgreSQL)

Core tables:

* `profiles` — employee data
* `user_roles` — access control
* `attendance` — time tracking
* `leave_requests`, `leave_balances`
* `payroll`
* `notifications`
* `todos`
* `resignation_requests`
* `departments`, `job_roles`
* `audit_logs`

---

##  Development Workflow

### Local Services

| Service    | Port |
| ---------- | ---- |
| Backend    | 3000 |
| ML Service | 8000 |
| Frontend   | 4200 |
| PostgreSQL | 5432 |
| Redis      | 6379 |

---

### Running the System

1. Start PostgreSQL + Redis
2. Run backend (`npm run dev`)
3. Run ML service (`uvicorn app.main:app --reload`)
4. Run Flutter web (`flutter run -d chrome`)

---

##  Important Directories

### Frontend

```
flutter_app/lib/features/
```

Contains all portals and feature modules.

### Backend

```
backend/src/modules/
```

Business logic grouped by domain.

### ML Service

```
ml_service/app/api/
```

All prediction endpoints.

---

##  Security Model

* JWT-based authentication
* Role-based authorization middleware
* Refresh token mechanism
* CORS restricted to frontend origin
* Password hashing via bcrypt

---

##  Performance Considerations

* PostgreSQL indexing on frequently queried fields
* Redis-backed job queues (BullMQ)
* ML service runs independently for scalability
* Frontend caching via Hive

---

##  Known Constraints

* System is **local-first** (not cloud-scaled yet)
* ML models rely on available dataset quality
* No real-time WebSocket notifications (polling used)
* OAuth2 is internal (no external providers)

---

## AI Assistant Guidelines

When interacting with this project:

* Always respect the **3-layer architecture**
* Do not bypass the backend when accessing ML
* Maintain strict **role-based access logic**
* Keep feature implementations modular per domain
* Follow existing folder structure conventions

---

##  Summary

SkillSync HRMS is a **production-grade, modular HR platform** combining:

* Modern frontend (Flutter Web)
* Scalable backend (Node.js + TypeScript)
* Intelligent ML layer (Python FastAPI)

It is designed to demonstrate:

* Full-stack engineering
* Clean architecture
* Applied machine learning in HR systems

---
