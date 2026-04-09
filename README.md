# AI-Powered HR Analytics Platform
Welcome to the HR Intelligence Suite — a modular, enterprise-grade HR analytics platform combining a Flutter frontend, a Node.js backend, and a specialized ML models layer featuring a RAG AI chatbot and four core predictive models. This repository is structured for parallel development across three technology stacks.

This repository contains a complete, modular HR analytics platform composed of three independent technology layers:

- **Frontend**: Flutter application (mobile, web, desktop)
- **Backend**: Node.js REST API + WebSocket server
- **ML Models**: Python microservice for predictive models + RAG AI chatbot

Each component resides in its own folder with dedicated documentation, dependencies, and setup instructions.

---

## 📁 Repository Structure
hr-analytics-platform/
├── frontend/ # Flutter application
├── backend/ # Node.js Fastify API
└── ml-models/ # Python ML microservice
---

# 🖥️ FRONTEND (Flutter)

## Overview
The Flutter frontend delivers a unified cross-platform experience for HR professionals and employees. It provides intuitive dashboards, real-time notifications, and interactive visualizations powered by the backend API and ML predictions.

## Tech Stack
- **Framework**: Flutter 3.19+ (Dart 3.3+)
- **State Management**: Riverpod 2.5+
- **Networking**: Dio 5.4+ with interceptors
- **Local Storage**: Hive 2.2+ (encrypted) + SharedPreferences
- **Charts**: fl_chart 0.68+
- **Routing**: GoRouter 14.0+
- **Notifications**: Firebase Cloud Messaging + local_notifications
- **Authentication**: OAuth2 PKCE + JWT refresh

## Key Features
- Role‑based dashboards (Employee, Manager, HR Admin)
- Real‑time turnover risk indicators and replacement rankings
- Skill gap explorer with DAG‑based progression paths
- Integrated RAG chatbot for HR policy Q&A
- Offline support with action queue
- Push notifications for critical HR events

## Architecture
frontend/
├── lib/
│ ├── core/ # DI, networking, routing, themes
│ ├── features/ # Auth, dashboard, employees, analytics, chatbot
│ └── models/ # Immutable data classes
├── assets/
├── pubspec.yaml
└── README.md # Detailed Flutter setup
## Setup Instructions
1. Install Flutter ≥3.19.0 from [flutter.dev](https://flutter.dev).
2. Navigate to the `frontend/` folder.
3. Run `flutter pub get`.
4. Create a `.env` file:
API_BASE_URL=https://api.yourdomain.com
OAUTH_CLIENT_ID=flutter_client
OAUTH_REDIRECT_URI=com.hrplatform.app:/oauth2redirect
5. For iOS: `cd ios && pod install`
6. Launch: `flutter run -d chrome` (web) or `flutter run` (mobile)

## Dependencies
```yaml
dependencies:
flutter: { sdk: flutter }
riverpod: ^2.5.1
dio: ^5.4.0
go_router: ^14.0.2
fl_chart: ^0.68.0
hive_flutter: ^1.1.0
firebase_messaging: ^14.7.0
flutter_local_notifications: ^17.0.0
jwt_decoder: ^2.0.1
freezed_annotation: ^2.4.1
json_annotation: ^4.8.1
API / Integration Points
Endpoint	Method	Description
/auth/token	POST	OAuth2 token exchange
/employees	GET	Paginated employee list
/employees/{id}/turnover-risk	GET	Risk score with SHAP factors
/employees/{id}/replacements	GET	Ranked internal candidates
/skills/gap	POST	Skill gap analysis
/chat/stream	WebSocket	RAG chatbot streaming
/notifications/subscribe	POST	Register FCM token
⚙️ BACKEND (Node.js)
Overview
The Node.js backend provides a secure, scalable API layer orchestrating business logic, database operations, and communication with the ML microservice. It handles authentication, authorization, real‑time events, and data aggregation.

Tech Stack
Runtime: Node.js 20.x (ES modules)

Framework: Fastify 4.x

Database: PostgreSQL 15 + Prisma ORM

Cache & Queue: Redis 7 + BullMQ

Real‑Time: WebSocket (@fastify/websocket)

Authentication: OAuth2 server (node‑oidc‑provider) + JWT

Validation: JSON Schema + TypeBox

Testing: Vitest + Supertest

Logging: Pino

Key Features
RESTful API with OpenAPI 3.1 documentation

Role‑Based Access Control (RBAC)

Audit logging for sensitive actions

WebSocket gateway for real‑time updates

Job queues for scheduled tasks (turnover recalculation)

File upload to S3‑compatible storage

gRPC client integration with ML service

Architecture
text
backend/
├── src/
│   ├── domain/             # Entities, repository interfaces
│   ├── application/        # Use cases
│   ├── infrastructure/     # Prisma, Redis, gRPC client
│   ├── interfaces/         # Fastify routes, WebSocket, OAuth2
│   └── config/             # Env, logger, swagger
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── tests/
├── package.json
└── README.md               # Detailed backend setup
Setup Instructions
Install Node.js 20, PostgreSQL 15, Redis 7.

Navigate to the backend/ folder.

Copy .env.example to .env and fill:

text
DATABASE_URL=postgresql://user:pass@localhost:5432/hr_platform
REDIS_URL=redis://localhost:6379
ML_SERVICE_GRPC=localhost:50051
npm install

npx prisma migrate deploy

npm run seed

npm run dev (listens on http://localhost:3000)

Dependencies
json
{
  "dependencies": {
    "@fastify/autoload": "^5.0.0",
    "@fastify/cors": "^9.0.0",
    "@fastify/swagger": "^8.14.0",
    "@fastify/websocket": "^8.3.0",
    "@grpc/grpc-js": "^1.9.0",
    "@prisma/client": "^5.10.0",
    "bullmq": "^5.0.0",
    "fastify": "^4.26.0",
    "ioredis": "^5.3.0",
    "jsonwebtoken": "^9.0.0",
    "oidc-provider": "^8.4.0",
    "pino": "^8.19.0",
    "zod": "^3.22.0"
  }
}
API / Integration Points
REST (base /api/v1)

Method	Endpoint	Description
GET	/employees	List employees
POST	/employees	Create employee
GET	/employees/:id/turnover	Turnover risk + SHAP
GET	/employees/:id/replacements	Replacement candidates
POST	/skills/analyze-gap	Skill gap report
GET	/learning/recommendations	Personalized learning
WebSocket	/ws	Chat & notifications
gRPC Interface (to ML service)

PredictTurnoverRisk

RankReplacements

AnalyzeSkillGap

GenerateLearningPath

🧠 ML MODELS + RAG AI Chatbot (Python)
Overview
The ML layer is a Python microservice hosting four specialized HR models and a Retrieval‑Augmented Generation (RAG) chatbot. It exposes a gRPC interface for inference and a WebSocket endpoint for streaming chat.

Tech Stack
Language: Python 3.11

ML: scikit‑learn, XGBoost 2.0+, LightGBM 4.3+

Deep Learning: PyTorch 2.2+ (embeddings)

Model Serving: gRPC, BentoML (optional)

Data: Pandas, NumPy, NetworkX

RAG: LangChain, FAISS, sentence‑transformers

LLM: Llama‑3‑8B‑Instruct (Ollama/vLLM)

Interpretability: SHAP 0.44+

Key Features
Turnover Prediction – XGBoost/LightGBM + SHAP

Internal Replacement Ranking – LightGBM LambdaMART

Skill Gap Analysis – DAG + Topological Sort

Training Recommendation – GBDT + Knowledge Graph

RAG AI Chatbot – Context‑aware HR assistant

Model versioning with A/B testing support

Detailed Models
1️⃣ Turnover Prediction
Algorithm: XGBoost / LightGBM ensemble + SHAP
References: Jain & Nayyar (2019); Lazzari et al. (2022); Lundberg & Lee (2017)

Predicts likelihood of voluntary turnover within 90 days using 27 engineered features (tenure, commute, skill alignment, etc.). Returns risk score (0‑100) and SHAP feature contributions.

2️⃣ Internal Replacement Ranking
Algorithm: LightGBM LambdaMART
References: Burges (2010); Lyzhin et al. (ICML 2023)

Learning‑to‑rank model that identifies best internal successors for a departing role, trained to optimize NDCG.

3️⃣ Skill Gap Analysis
Algorithm: DAG + Topological Sort
References: Liu et al. (2023); KG‑PLPPM (2025)

Constructs a directed acyclic graph of skill prerequisites, then performs topological sort to recommend optimal learning order for skill gaps.

4️⃣ Training Recommendation
Algorithm: GBDT + Knowledge Graph
References: Nabizadeh et al. (2020); Wang et al. (2023)

Hybrid recommender that combines collaborative filtering (GBDT) with a knowledge graph to suggest personalized courses, certifications, and mentorships.

5️⃣ RAG AI Chatbot
Framework: LangChain + FAISS + Llama‑3‑8B‑Instruct

Retrieval‑augmented chatbot that answers HR policy questions using vectorized documents. Employee‑specific data is fetched via secure function calling, never sent to the LLM.

Architecture
text
ml-models/
├── src/
│   ├── models/             # Model classes (XGB, LGBM, LambdaMART, GBDT)
│   ├── services/           # gRPC server, chatbot WebSocket
│   ├── rag/                # LangChain pipeline, FAISS index
│   ├── dag/                # Skill graph and topological sort
│   └── proto/              # gRPC protocol definitions
├── models/                 # Serialized model artifacts
├── data/                   # Knowledge graph, FAISS index
├── requirements.txt
├── Dockerfile
└── README.md               # Detailed ML setup
Setup Instructions
Python 3.11 and Docker (recommended).

Navigate to ml-models/.

Create venv: python -m venv venv && source venv/bin/activate

pip install -r requirements.txt

Download pre‑trained artifacts into models/ (see internal docs).

Start gRPC server: python -m src.server

Start chatbot WebSocket: python -m src.chatbot

Dependencies
text
xgboost==2.0.3
lightgbm==4.3.0
shap==0.44.0
scikit-learn==1.4.1.post1
pandas==2.2.0
numpy==1.26.3
networkx==3.2.1
grpcio==1.60.0
grpcio-tools==1.60.0
langchain==0.1.0
langchain-community==0.0.10
faiss-cpu==1.7.4
sentence-transformers==2.2.2
torch==2.2.0
bentoml==1.1.0
API / Integration Points
gRPC Port: 50051 (exposed to backend)

WebSocket Port: 50052 (exposed to frontend for chat)

Health probe: gRPC health check on 50051

📄 License & Acknowledgments
This platform is proprietary software. Methodologies are based on peer‑reviewed research cited in each model description.

For questions or contributions, contact the platform engineering team.

Generated by technical documentation expert – ready for production use.

text
Can you make it as a one cell the whole project
We need to produce a single comprehensive README file that covers all three technology layers, but the user wants it as "one cell" meaning a single markdown document that can be copied and pasted as a whole. The user previously said "make sure to make each technology stack in a separate folder" but now wants "as a one cell the whole project." Possibly they want a single README.md file that describes the entire project with the three folders, not separate READMEs in each folder. The previous response already had a single README covering all three sections with separate headings. The user might want that exact content as a single block.

I'll provide a complete README.md content that includes all sections, ready to copy and paste. I'll ensure it's well-structured with proper markdown formatting.

Here is the complete, copy‑paste‑ready README.md file for the entire AI‑Powered HR Analytics Platform. It covers all three technology stacks in one document, as requested.

markdown
# AI-Powered HR Analytics Platform

This repository contains a complete, modular HR analytics platform composed of three independent technology layers, each in its own folder:

- **Frontend**: Flutter application (mobile, web, desktop)
- **Backend**: Node.js REST API + WebSocket server
- **ML Models**: Python microservice for predictive models + RAG AI chatbot

Each component can be developed, deployed, and scaled independently. This README provides a unified overview and setup guide for the entire system.

---

## 📁 Repository Structure
hr-analytics-platform/
├── frontend/ # Flutter application
├── backend/ # Node.js Fastify API
└── ml-models/ # Python ML microservice

text

---

# 🖥️ FRONTEND (Flutter)

## Overview
The Flutter frontend delivers a unified cross-platform experience for HR professionals and employees. It provides intuitive dashboards, real-time notifications, and interactive visualizations powered by the backend API and ML predictions.

## Tech Stack
- **Framework**: Flutter 3.19+ (Dart 3.3+)
- **State Management**: Riverpod 2.5+
- **Networking**: Dio 5.4+ with interceptors
- **Local Storage**: Hive 2.2+ (encrypted) + SharedPreferences
- **Charts**: fl_chart 0.68+
- **Routing**: GoRouter 14.0+
- **Notifications**: Firebase Cloud Messaging + local_notifications
- **Authentication**: OAuth2 PKCE + JWT refresh

## Key Features
- Role‑based dashboards (Employee, Manager, HR Admin)
- Real‑time turnover risk indicators and replacement rankings
- Skill gap explorer with DAG‑based progression paths
- Integrated RAG chatbot for HR policy Q&A
- Offline support with action queue
- Push notifications for critical HR events

## Architecture
frontend/
├── lib/
│ ├── core/ # DI, networking, routing, themes
│ ├── features/ # Auth, dashboard, employees, analytics, chatbot
│ └── models/ # Immutable data classes
├── assets/
├── pubspec.yaml
└── README.md # Detailed Flutter setup

text

## Setup Instructions
1. Install Flutter ≥3.19.0 from [flutter.dev](https://flutter.dev).
2. Navigate to the `frontend/` folder.
3. Run `flutter pub get`.
4. Create a `.env` file:
API_BASE_URL=https://api.yourdomain.com
OAUTH_CLIENT_ID=flutter_client
OAUTH_REDIRECT_URI=com.hrplatform.app:/oauth2redirect

text
5. For iOS: `cd ios && pod install`
6. Launch: `flutter run -d chrome` (web) or `flutter run` (mobile)

## Dependencies
```yaml
dependencies:
flutter: { sdk: flutter }
riverpod: ^2.5.1
dio: ^5.4.0
go_router: ^14.0.2
fl_chart: ^0.68.0
hive_flutter: ^1.1.0
firebase_messaging: ^14.7.0
flutter_local_notifications: ^17.0.0
jwt_decoder: ^2.0.1
freezed_annotation: ^2.4.1
json_annotation: ^4.8.1
API / Integration Points
Endpoint	Method	Description
/auth/token	POST	OAuth2 token exchange
/employees	GET	Paginated employee list
/employees/{id}/turnover-risk	GET	Risk score with SHAP factors
/employees/{id}/replacements	GET	Ranked internal candidates
/skills/gap	POST	Skill gap analysis
/chat/stream	WebSocket	RAG chatbot streaming
/notifications/subscribe	POST	Register FCM token
⚙️ BACKEND (Node.js)
Overview
The Node.js backend provides a secure, scalable API layer orchestrating business logic, database operations, and communication with the ML microservice. It handles authentication, authorization, real‑time events, and data aggregation.

Tech Stack
Runtime: Node.js 20.x (ES modules)

Framework: Fastify 4.x

Database: PostgreSQL 15 + Prisma ORM

Cache & Queue: Redis 7 + BullMQ

Real‑Time: WebSocket (@fastify/websocket)

Authentication: OAuth2 server (node‑oidc‑provider) + JWT

Validation: JSON Schema + TypeBox

Testing: Vitest + Supertest

Logging: Pino

Key Features
RESTful API with OpenAPI 3.1 documentation

Role‑Based Access Control (RBAC)

Audit logging for sensitive actions

WebSocket gateway for real‑time updates

Job queues for scheduled tasks (turnover recalculation)

File upload to S3‑compatible storage

gRPC client integration with ML service

Architecture
text
backend/
├── src/
│   ├── domain/             # Entities, repository interfaces
│   ├── application/        # Use cases
│   ├── infrastructure/     # Prisma, Redis, gRPC client
│   ├── interfaces/         # Fastify routes, WebSocket, OAuth2
│   └── config/             # Env, logger, swagger
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── tests/
├── package.json
└── README.md               # Detailed backend setup
Setup Instructions
Install Node.js 20, PostgreSQL 15, Redis 7.

Navigate to the backend/ folder.

Copy .env.example to .env and fill:

text
DATABASE_URL=postgresql://user:pass@localhost:5432/hr_platform
REDIS_URL=redis://localhost:6379
ML_SERVICE_GRPC=localhost:50051
npm install

npx prisma migrate deploy

npm run seed

npm run dev (listens on http://localhost:3000)

Dependencies
json
{
  "dependencies": {
    "@fastify/autoload": "^5.0.0",
    "@fastify/cors": "^9.0.0",
    "@fastify/swagger": "^8.14.0",
    "@fastify/websocket": "^8.3.0",
    "@grpc/grpc-js": "^1.9.0",
    "@prisma/client": "^5.10.0",
    "bullmq": "^5.0.0",
    "fastify": "^4.26.0",
    "ioredis": "^5.3.0",
    "jsonwebtoken": "^9.0.0",
    "oidc-provider": "^8.4.0",
    "pino": "^8.19.0",
    "zod": "^3.22.0"
  }
}
API / Integration Points
REST (base /api/v1)

Method	Endpoint	Description
GET	/employees	List employees
POST	/employees	Create employee
GET	/employees/:id/turnover	Turnover risk + SHAP
GET	/employees/:id/replacements	Replacement candidates
POST	/skills/analyze-gap	Skill gap report
GET	/learning/recommendations	Personalized learning
WebSocket	/ws	Chat & notifications
gRPC Interface (to ML service)

PredictTurnoverRisk

RankReplacements

AnalyzeSkillGap

GenerateLearningPath

🧠 ML MODELS + RAG AI Chatbot (Python)
Overview
The ML layer is a Python microservice hosting four specialized HR models and a Retrieval‑Augmented Generation (RAG) chatbot. It exposes a gRPC interface for inference and a WebSocket endpoint for streaming chat.

Tech Stack
Language: Python 3.11

ML: scikit‑learn, XGBoost 2.0+, LightGBM 4.3+

Deep Learning: PyTorch 2.2+ (embeddings)

Model Serving: gRPC, BentoML (optional)

Data: Pandas, NumPy, NetworkX

RAG: LangChain, FAISS, sentence‑transformers

LLM: Llama‑3‑8B‑Instruct (Ollama/vLLM)

Interpretability: SHAP 0.44+

Key Features
Turnover Prediction – XGBoost/LightGBM + SHAP

Internal Replacement Ranking – LightGBM LambdaMART

Skill Gap Analysis – DAG + Topological Sort

Training Recommendation – GBDT + Knowledge Graph

RAG AI Chatbot – Context‑aware HR assistant

Model versioning with A/B testing support

Detailed Models
1️⃣ Turnover Prediction
Algorithm: XGBoost / LightGBM ensemble + SHAP
References: Jain & Nayyar (2019); Lazzari et al. (2022); Lundberg & Lee (2017)

Predicts likelihood of voluntary turnover within 90 days using 27 engineered features (tenure, commute, skill alignment, etc.). Returns risk score (0‑100) and SHAP feature contributions.

2️⃣ Internal Replacement Ranking
Algorithm: LightGBM LambdaMART
References: Burges (2010); Lyzhin et al. (ICML 2023)

Learning‑to‑rank model that identifies best internal successors for a departing role, trained to optimize NDCG.

3️⃣ Skill Gap Analysis
Algorithm: DAG + Topological Sort
References: Liu et al. (2023); KG‑PLPPM (2025)

Constructs a directed acyclic graph of skill prerequisites, then performs topological sort to recommend optimal learning order for skill gaps.

4️⃣ Training Recommendation
Algorithm: GBDT + Knowledge Graph
References: Nabizadeh et al. (2020); Wang et al. (2023)

Hybrid recommender that combines collaborative filtering (GBDT) with a knowledge graph to suggest personalized courses, certifications, and mentorships.

5️⃣ RAG AI Chatbot
Framework: LangChain + FAISS + Llama‑3‑8B‑Instruct

Retrieval‑augmented chatbot that answers HR policy questions using vectorized documents. Employee‑specific data is fetched via secure function calling, never sent to the LLM.

Architecture
text
ml-models/
├── src/
│   ├── models/             # Model classes (XGB, LGBM, LambdaMART, GBDT)
│   ├── services/           # gRPC server, chatbot WebSocket
│   ├── rag/                # LangChain pipeline, FAISS index
│   ├── dag/                # Skill graph and topological sort
│   └── proto/              # gRPC protocol definitions
├── models/                 # Serialized model artifacts
├── data/                   # Knowledge graph, FAISS index
├── requirements.txt
├── Dockerfile
└── README.md               # Detailed ML setup
Setup Instructions
Python 3.11 and Docker (recommended).

Navigate to ml-models/.

Create venv: python -m venv venv && source venv/bin/activate

pip install -r requirements.txt

Download pre‑trained artifacts into models/ (see internal docs).

Start gRPC server: python -m src.server

Start chatbot WebSocket: python -m src.chatbot

Dependencies
text
xgboost==2.0.3
lightgbm==4.3.0
shap==0.44.0
scikit-learn==1.4.1.post1
pandas==2.2.0
numpy==1.26.3
networkx==3.2.1
grpcio==1.60.0
grpcio-tools==1.60.0
langchain==0.1.0
langchain-community==0.0.10
faiss-cpu==1.7.4
sentence-transformers==2.2.2
torch==2.2.0
bentoml==1.1.0
API / Integration Points
gRPC Port: 50051 (exposed to backend)

WebSocket Port: 50052 (exposed to frontend for chat)

Health probe: gRPC health check on 50051

📄 License & Acknowledgments
This platform is proprietary software. Methodologies are based on peer‑reviewed research cited in each model description.

For questions or contributions, contact the platform engineering team.

Generated by technical documentation expert – ready for production use.

text
