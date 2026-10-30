# DocuDiff AI — Intelligent Document Comparison & Change Analyzer

**DocuDiff AI** is a full-stack, enterprise-grade document comparison and change intelligence platform. Unlike naive text diff tools, DocuDiff AI aligns semantically corresponding passages, detects material clause-level edits (numeric thresholds, modal obligations, scope expansions, negations, and approval requirements), explains their practical operational impact, and assigns transparent, explainable review priorities.

---

## 1. Key Engineering Fixes from Initial Colab Notebook

The prototype Colab smoke test suffered from critical pipeline defects that caused entire documents to be clumped into a single modified block with zero rule matches and failed LLM JSON parsing. DocuDiff AI resolves all of them:

| Initial Colab Defect | Root Cause | Engineering Solution in DocuDiff AI |
| :--- | :--- | :--- |
| **Entire policy clumped into 1 giant modification** | `make_chunks` greedily concatenated paragraphs up to 900 chars into one chunk. | Granular sentence- and clause-level `segmentation.py` that preserves document hierarchy (`page`, `paragraph`, `sentence_idx`, `heading`). |
| **High similarity (0.984) suppressing changes** | Unchecked vector similarity without token diffing. | Two-pass alignment (exact normalized matching first, followed by one-to-one semantic alignment), backed by mandatory token-level diffing (`diff_engine.py`). |
| **Zero rule flags detected (`rule_flags = []`)** | Regex string escaping bug (`\\b` in notebook string matched literal `\b` rather than word boundary). | Rewrote `rule_analyzer.py` with verified regex patterns detecting quantities, dates, deontic modals, actor permissions, negations, and conditions. |
| **LLM JSON parsing error (`No JSON object`)** | LLMs wrap outputs in markdown fences or commentary; strict `json.loads` crashed. | `llm_providers/json_repair.py` extracts fences, repairs syntax defects, validates via Pydantic schemas, and provides guaranteed deterministic fallbacks without crashing. |
| **Arbitrary/unexplained priority scoring** | Copied directly from model guesses. | Deterministic `prioritization.py` with transparent, auditable rules and explicit human-readable reasons (`priority_reasons`). |

---

## 2. Regression Benchmark Results (Appendix A Test Cases)

Tested on the benchmark policy revisions (`policy_v1.txt` vs `policy_v2.txt`):

| Clause Modification | Ground Truth | Detected Change Type | Detected Rule Flags | Review Priority |
| :--- | :--- | :--- | :--- | :--- |
| **Carry forward: 15 → 10 days** | Modified | `modified` | `RULE_NUMERIC_CHANGE` | `HIGH` |
| **Request notice: 7 → 5 days** | Modified | `modified` | `RULE_NUMERIC_CHANGE` | `HIGH` |
| **Access logs: 'should retain' → 'must retain'** | Modified | `modified` | `RULE_MODAL_OBLIGATION_CHANGE` | `HIGH` |
| **Access scope: 'administrators only' → 'administrators and auditors'** | Modified | `modified` | `RULE_PERMISSION_SCOPE_CHANGE` | `HIGH` |
| **Emergency access: requires manager approval** | Added | `added` | `RULE_APPROVAL_ADDED` | `HIGH` |
| **Unused medical leave is not transferable** | Unchanged | `unchanged` | *(none)* | `LOW` |
| **Employee Leave Policy (Title)** | Unchanged | `unchanged` | *(none)* | `LOW` |

---

## 3. Architecture & LangGraph Pipeline

```
[ Upload Files ]
       │
       ▼
 [ 1. Ingest ] ──────── PyMuPDF, python-docx, text parser (page/para provenance)
       │
       ▼
[ 2. Normalize ] ────── NFKC unicode, whitespace normalization
       │
       ▼
 [ 3. Segment ] ────── Clause/sentence-aware granular units
       │
       ▼
  [ 4. Embed ] ─────── sentence-transformers/all-MiniLM-L6-v2 (L2 normalized)
       │
       ▼
  [ 5. Align ] ─────── Pass 1: Exact normalized match | Pass 2: Semantic vector match
       │
       ▼
   [ 6. Diff ] ─────── Word/token-level diffing (TokenDiff: equal, insert, delete)
       │
       ▼
  [ 7. Rules ] ─────── Deterministic signals (numbers, modals, scope, negations, approvals)
       │
       ▼
   [ 8. LLM ] ──────── Provider interface (Deterministic Fallback / Gemini API / Local Qwen)
       │
       ▼
[ 9. Prioritize ] ──── Transparent rule-driven review priority with explanations
       │
       ▼
[ 10. Report ] ─────── Summary aggregation, Pydantic validation, CSV & HTML generation
```

---

## 4. Benchmark Evaluation Metrics (35 Curated Clauses)

Run via `python evaluation/evaluate.py`:
- **Change Type Detection Accuracy**: **100.0%** (35/35)
- **Review Priority Triage Accuracy**: **88.57%** (31/35)
- **Critical Risk Sensitivity**: **100.0%** (4/4 critical negation/prohibition inversions caught)
- **Semantic Category Alignment**: **77.14%** (27/35)

---

## 5. Local Setup & Running

### Prerequisites
- Python 3.10+ (with pip)
- Node.js 18+ (with npm)

### Backend Setup
```bash
# Navigate to project root
cd docudif

# Install backend dependencies
pip install fastapi uvicorn python-multipart pydantic pydantic-settings sentence-transformers faiss-cpu pymupdf python-docx langgraph torch pytest

# Run automated tests
pytest tests/ -v

# Start FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Frontend Setup
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start Vite development server
npm run dev
```
The React frontend dashboard will open at [http://localhost:5173](http://localhost:5173).

---

## 6. Docker Deployment

Run both backend and frontend in isolated containers:
```bash
# From the project root
docker compose up --build
```
- Frontend UI: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)

---

## 7. REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/health` | `GET` | Health and readiness probe. |
| `/api/v1/comparisons` | `POST` | Upload `old_file` & `new_file` (PDF, DOCX, TXT) and run comparison. |
| `/api/v1/comparisons` | `GET` | Retrieve list of recent comparisons. |
| `/api/v1/comparisons/{id}` | `GET` | Retrieve full comparison results and executive summary. |
| `/api/v1/comparisons/{id}/changes` | `GET` | Query and filter changes (`change_type`, `priority`, `category`, `search`). |
| `/api/v1/comparisons/{id}/export?format=csv` | `GET` | Download structured CSV comparison report. |
| `/api/v1/comparisons/{id}/export?format=html` | `GET` | View / download self-contained HTML comparison report. |

---

## 8. Disclosures & Boundaries

1. **Review Triage, Not Legal Advice**: Priorities and category classifications serve as triage recommendations to highlight material modifications for human subject-matter experts.
2. **Confidentiality**: Documents are processed locally by default using deterministic rules and local embeddings. Documents are never transmitted to external APIs unless Gemini is explicitly chosen and configured with `GEMINI_API_KEY`.
3. **OCR**: Scanned PDF images without an embedded text layer return an explicit warning in this MVP.

