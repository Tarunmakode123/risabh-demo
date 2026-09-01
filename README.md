# Enterprise Internal Email Interaction Automation Bot

Production-quality internal email interaction automation system designed for **ArrowMail / GreenArrow** sending infrastructure testing and server warming.

---

## 🎯 Architecture & Workflow

```text
ArrowMail / GreenArrow ──► Test Inbox (IMAP) ──► Deduplication ──► MIME Parser ──► Campaign Matcher
                                                                                         │
COMPLETED ◄── Threaded SMTP Reply ◄── Audit Log ◄── Playwright CTA ◄── Domain Validation ◄───────┘
```

The system operates strictly against **mailboxes, domains, and CTA destinations explicitly configured by the administrator**.

---

## 📂 Project Directory Structure

```text
risabh-demo/
├── backend/                     # FastAPI API Server & Services
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint & router registry
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy PostgreSQL connection
│   │   ├── models.py            # Database schema models
│   │   ├── schemas.py           # Pydantic API schemas
│   │   ├── security.py          # JWT, bcrypt, Fernet credential encryption
│   │   ├── dependencies.py      # FastAPI auth & DB session dependencies
│   │   ├── api/                 # Auth, Accounts, Emails, Settings, Dashboard, System Routers
│   │   └── services/            # IMAP, MIME Parser, Deduplication, SMTP, CTA, Workflow State Machine
│   ├── requirements.txt
│   └── Dockerfile
├── worker/                      # Celery Async Worker & Playwright Engine
│   ├── celery_app.py            # Celery app with Redis broker & queue routing
│   ├── imap_worker.py           # IMAP poller task
│   ├── cta_worker.py            # CTA extraction & Playwright worker
│   ├── reply_worker.py          # Threaded SMTP reply worker
│   ├── workflow_worker.py       # State orchestrator task
│   ├── playwright_engine.py    # Playwright browser engine & redirect validator
│   ├── browser_context.py       # Isolated browser context & screenshot capture
│   └── Dockerfile
├── frontend/                    # React (Vite + Tailwind CSS) Dashboard
│   ├── src/
│   │   ├── components/          # StatCards, ActivityTable, Navbar
│   │   ├── pages/               # DashboardPage, InboxesPage, EmailLogsPage, SettingsPage, LoginPage
│   │   ├── services/            # Axios API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
├── tests/                       # Test Suite
│   ├── test_parser.py           # Email MIME parsing tests
│   ├── test_cta_validator.py   # Domain allowlist & redirect validation tests
│   ├── test_deduplication.py    # Message-ID deduplication tests
│   ├── test_workflow.py         # State machine transition tests
│   └── test_e2e_synthetic.py    # Synthetic End-to-End Pipeline test
├── docker/
│   └── nginx.conf               # Nginx reverse proxy
├── docker-compose.yml           # Full stack compose deployment
├── .env.example                 # Environment configuration template
└── README.md
```

---

## 🔒 Security Guarantees & Technical Controls

1. **Strict URL Domain Validation**:
   - `ALLOWED_CTA_DOMAINS` parsing using Python `urllib.parse.urlparse` to extract normalized hostnames.
   - Rejects lookalikes (e.g. `test.example.com.evil.com` or `evil.com/?redirect=test.example.com`).
   - Validates destination URLs **both before navigation and on every HTTP redirect**.
2. **Encrypted Credentials**:
   - Mailbox passwords stored encrypted using Fernet authenticated symmetric key encryption.
3. **Idempotency & Deduplication**:
   - Database unique constraint on `(account_id, message_id)`. Incoming emails with duplicate `Message-ID` headers are ignored.
4. **PostgreSQL Authoritative State Engine**:
   - Uses `SELECT ... FOR UPDATE SKIP LOCKED` inside transactional boundaries so multiple Celery workers can never process the same email concurrently.
5. **Emergency Kill Switch**:
   - Global pause toggle (`POST /api/system/pause`) to immediately halt Playwright browser execution and SMTP auto-replies.

---

## 🚀 Quickstart & Docker Deployment

### 1. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Launch with Docker Compose
```bash
docker compose up -d
```
Services launched:
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`
- **FastAPI Backend**: `http://localhost:8000`
- **React Frontend**: `http://localhost:3000`
- **Nginx Reverse Proxy**: `http://localhost:80`

### 3. Login Credentials
Default Admin Credentials:
- **Username**: `admin`
- **Password**: `admin123`

---

## 🧪 Running Automated Tests

Run the unit tests and synthetic E2E pipeline test:

```bash
python tests/test_parser.py
python tests/test_cta_validator.py
python tests/test_deduplication.py
python tests/test_workflow.py
python tests/test_e2e_synthetic.py
```
