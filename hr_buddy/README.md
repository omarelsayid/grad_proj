# HR Buddy — Document-Grounded RAG Chatbot

HR Buddy is a FastAPI + ChromaDB RAG service that answers employee questions using **only** the SkillSync Company Policy PDF.  
It integrates with the SkillSync Flutter app via a floating chat button visible in all three portals.

---

## Architecture

```
SkillSync_Company_Policy_2026.pdf
         │
         ▼
  [pdf_ingest.py]              pypdf → page-aware chunking (700 chars, 150 overlap)
         │
         ▼
  [sentence-transformers]      all-MiniLM-L6-v2 local embedding (no API key needed)
         │
         ▼
  [ChromaDB]                   persistent local vector store  (./app/data/chroma)
         │
         ▼
  [FastAPI /chat]              retrieve top-5 → build grounded prompt → LLM (OpenAI-compat)
         │
         ▼
  Flutter HrBuddyChatScreen    answer + citation chips (Page N)
```

---

## Quick Start

### 1 — Install dependencies

```bash
cd hr_buddy/backend
py -m pip install -r requirements.txt
```

### 2 — Configure environment

```bash
cp .env.example .env
```

Edit `.env` — minimum required for offline fallback mode (no LLM key needed):

```env
EMBEDDING_PROVIDER=local
PDF_PATH=../../SkillSync_Company_Policy_2026.pdf
```

To enable full LLM-generated answers (recommended), add one of:

```env
# OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Groq (free tier, fast)
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.1-8b-instant

# Ollama (fully local)
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
```

### 3 — Start the backend

```bash
cd hr_buddy/backend
uvicorn app.main:app --port 8001 --reload
```

### 4 — Ingest the PDF (one-time, or after PDF update)

```bash
curl -X POST http://localhost:8001/ingest-pdf
```

Or from the Flutter app: tap **HR Buddy** → tap **Ingest PDF** in the app bar.

### 5 — Test it

```bash
# Health check
curl http://localhost:8001/health

# Ask a question
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many annual leave days do I get?"}'

# Ask about resignation
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the resignation notice period?"}'

# Ask about skill chains
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are skill chains?"}'
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Index readiness + chunk count |
| POST | `/ingest-pdf` | Load PDF → chunk → embed → store |
| POST | `/chat` | RAG chat (returns answer + citations) |
| DELETE | `/reset-index` | Clear ChromaDB (then re-ingest) |

### `/chat` request

```json
{
  "message": "How many annual leave days do I get?",
  "session_id": "optional-user-id"
}
```

### `/chat` response

```json
{
  "answer": "You are entitled to 21 annual leave days per year.\n\nFull-time employees accrue leave ...\n\nSource: Page 9",
  "citations": [
    { "page": 9, "snippet": "Annual Leave: Full-time employees are entitled to 21 days..." },
    { "page": 10, "snippet": "Leave must be approved by your direct manager..." }
  ],
  "matched_chunks": ["...raw chunk text..."]
}
```

---

## Sample Questions (from the policy doc)

- How many annual leave days do I get?
- What is the resignation notice period?
- What are skill chains?
- How do I access learning resources?
- What happens if I am late to work?
- What are the criticality tiers for skill gaps?
- Can I work remotely?
- What is the compassionate leave allowance?
- How does turnover prediction work?

---

## Flutter Integration

The HR Buddy button appears as a floating action button (`FloatingActionButton.extended`) in every portal shell.

- Tap it → `HrBuddyChatScreen` opens as a full-screen page
- The welcome screen shows 6 suggested questions
- Every answer shows **Page N** citation chips; tap a chip to see the source snippet
- If the index isn't ready, a banner prompts you to tap **Ingest PDF**
- Backend URL is set in `lib/services/hr_buddy_service.dart` → `_baseUrl`

```
skillsync_flutter/lib/
  models/chat_models.dart          ← ChatMessage, ChatCitation, ChatResponse
  services/hr_buddy_service.dart   ← HTTP client (isReady, ingestPdf, sendMessage)
  widgets/chat_bubble.dart         ← ChatBubble, TypingIndicator, _CitationChip
  presentation/hr_buddy/
    screen.dart                    ← HrBuddyChatScreen (full chat UI)
```

---

## Docker (optional)

```bash
cd hr_buddy/backend
docker build -t hr-buddy .
docker run -p 8001:8001 \
  -v $(pwd)/app/data/chroma:/app/app/data/chroma \
  -v $(pwd)/../../SkillSync_Company_Policy_2026.pdf:/pdf/policy.pdf \
  -e PDF_PATH=/pdf/policy.pdf \
  -e LLM_BASE_URL=https://api.openai.com/v1 \
  -e LLM_API_KEY=sk-... \
  hr-buddy
```

---

## Running Tests

```bash
cd hr_buddy/backend
py -m pytest tests/ -v
```

---

## Fallback Mode (no LLM key)

If `LLM_BASE_URL` or `LLM_API_KEY` is not set, HR Buddy returns the top retrieved chunk directly with its page number — no LLM call is made. This is useful for demos or when you want zero external API cost.
