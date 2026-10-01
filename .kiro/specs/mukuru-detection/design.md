# Mukuru Detection — Technical Design
> Version: 1.0 | Hackathon MVP

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser / Client                          │
│                                                                   │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│   │  React Web   │  │ USSD Simulator│  │   SMS Simulator     │  │
│   │  App (Vite + │  │ (phone-shaped │  │  (phone-shaped UI)  │  │
│   │  Tailwind)   │  │   UI)        │  │                     │  │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘  │
└──────────┼─────────────────┼──────────────────────┼─────────────┘
           │  HTTP / JSON    │                      │
           ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend  :8000                        │
│                                                                   │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │  Auth /    │ │  Scan    │ │  Txn     │ │  USSD / SMS      │ │
│  │  Accounts  │ │  Router  │ │  Router  │ │  Routers         │ │
│  └─────┬──────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│        │              │            │                 │           │
│        └──────────────┴────────────┴─────────────────┘          │
│                              │                                    │
│              ┌───────────────▼──────────────────┐                │
│              │         Risk Engine               │                │
│              │  (pure Python, no FastAPI deps)   │                │
│              │                                   │                │
│              │  ┌─────────────┐ ┌─────────────┐ │                │
│              │  │ Rules Layer │ │  Classifier  │ │                │
│              │  │ (patterns,  │ │  (TF-IDF +   │ │                │
│              │  │  keywords,  │ │  log.reg.)   │ │                │
│              │  │  URL check) │ └──────┬───────┘ │                │
│              │  └──────┬──────┘        │ blend   │                │
│              │         └───────────────┘         │                │
│              │         (optional LLM fallback)   │                │
│              └───────────────────────────────────┘                │
│                              │                                    │
│              ┌───────────────▼──────────────────┐                │
│              │      SQLAlchemy + SQLite          │                │
│              │  users, sessions, scans, txns,    │                │
│              │  sms_outbox, audit_log            │                │
│              └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

**Key constraints:**
- The risk engine (`backend/engine/`) is a pure Python package — zero FastAPI imports.
- Backend and frontend communicate only over HTTP/JSON. No shared Python imports.
- All human-readable strings live in `i18n/<lang>.json`. The API returns codes.

---

## 2. Repository Layout

```
Mukuru-Detection/
├── backend/
│   ├── main.py                  # FastAPI app factory, CORS, lifespan
│   ├── config.py                # Settings (pydantic-settings, reads .env)
│   ├── database.py              # SQLAlchemy engine + session factory
│   ├── models/
│   │   ├── user.py              # User, Session ORM models
│   │   ├── scan.py              # ScanResult ORM model
│   │   ├── transaction.py       # Transaction ORM model
│   │   └── sms.py               # SMSMessage ORM model
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   ├── routers/
│   │   ├── auth.py              # /register, /login, /accounts/me
│   │   ├── scan.py              # /scan
│   │   ├── transactions.py      # /transactions/check, /transactions/send
│   │   ├── ussd.py              # /ussd
│   │   ├── sms.py               # /sms/inbound, /sms/outbox
│   │   ├── panic.py             # /panic
│   │   ├── login_guard.py       # /login-guard/event
│   │   └── library.py           # /scams/library
│   ├── engine/                  # Pure Python risk engine
│   │   ├── __init__.py
│   │   ├── rules.py             # Rule functions, weight maps
│   │   ├── url_check.py         # URL extraction + Safe Browsing / mock
│   │   ├── email_checks.py      # Email-specific signal checks
│   │   ├── classifier.py        # Load model, predict, blend scores
│   │   ├── transaction_rules.py # Transaction risk rules
│   │   └── language_detect.py   # Lightweight language detection
│   ├── decoy/
│   │   └── generator.py         # Fixed-seed decoy account + history
│   ├── model/
│   │   └── classifier.pkl       # Trained model artifact (gitignored binary)
│   ├── seed.py                  # One-command demo seed script
│   └── tests/
│       ├── test_rules.py
│       ├── test_transaction_rules.py
│       ├── test_duress.py
│       ├── test_i18n_parity.py
│       └── test_e2e_demo.py
├── web/
│   ├── src/
│   │   ├── api/                 # Typed API client (fetch wrappers)
│   │   ├── components/          # Shared UI components
│   │   ├── pages/               # One file per screen
│   │   ├── i18n/                # Frontend i18n loader (reads JSON files)
│   │   └── App.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── shared/
│   └── reason_codes.json        # Frozen vocabulary (source of truth)
├── i18n/
│   ├── en.json
│   ├── zu.json
│   └── ... (6 draft files)
├── data/
│   ├── scam_samples.json
│   ├── legit_samples.json
│   └── scam_library.json
├── docs/
│   ├── api_contract.md
│   ├── README.md
│   └── demo_script.md
├── scripts/
│   ├── train_classifier.py
│   └── evaluate_classifier.py
├── .env.example
└── .gitignore
```

---

## 3. Data Models (SQLAlchemy)

### 3.1 User

| Column          | Type        | Notes                                      |
|-----------------|-------------|--------------------------------------------|
| id              | UUID (PK)   |                                            |
| phone           | String(20)  | Unique, E.164 format                       |
| pin_hash        | String(128) | bcrypt/argon2 hash                         |
| duress_pin_hash | String(128) | bcrypt/argon2 hash; must differ from PIN   |
| country         | String(2)   | ISO 3166-1 alpha-2                         |
| language        | String(5)   | BCP-47 (en, zu, fr, sw, st, hi, nl, pt)   |
| trusted_contact | String(20)  | Phone number for silent alert              |
| is_in_duress    | Boolean     | Runtime flag; not persisted between logins |
| created_at      | DateTime    |                                            |

### 3.2 UserSession

| Column      | Type      | Notes                         |
|-------------|-----------|-------------------------------|
| id          | UUID (PK) |                               |
| user_id     | FK→User   |                               |
| token       | String    | Opaque bearer token           |
| is_duress   | Boolean   | Duress flag for this session  |
| expires_at  | DateTime  |                               |
| created_at  | DateTime  |                               |

### 3.3 ScanResult

| Column             | Type      | Notes                              |
|--------------------|-----------|------------------------------------|
| id                 | UUID (PK) |                                    |
| user_id            | FK→User   | Nullable (anonymous scan allowed)  |
| text_hash          | String    | SHA-256 of input (never store raw) |
| channel            | String    | web/ussd/sms/email                 |
| score              | Integer   | 0–100                              |
| tier               | String    | SAFE/CAUTION/HIGH_RISK             |
| category           | String    |                                    |
| reasons            | JSON      | List of reason codes (max 3)       |
| advice             | JSON      | List of advice codes               |
| explanation_source | String    | rules/llm                          |
| created_at         | DateTime  |                                    |

### 3.4 Transaction

| Column        | Type      | Notes                                 |
|---------------|-----------|---------------------------------------|
| id            | UUID (PK) |                                       |
| user_id       | FK→User   |                                       |
| recipient     | String    | Phone or account reference            |
| amount        | Decimal   |                                       |
| currency      | String(3) | ZAR, USD, ZWL …                       |
| country       | String(2) | Destination country                   |
| status        | String    | pending/completed/decoy               |
| is_decoy      | Boolean   | True if executed in duress mode       |
| created_at    | DateTime  |                                       |

### 3.5 SMSMessage

| Column      | Type      | Notes                         |
|-------------|-----------|-------------------------------|
| id          | UUID (PK) |                               |
| user_id     | FK→User   |                               |
| direction   | String    | inbound/outbound              |
| body        | Text      |                               |
| sender      | String    |                               |
| created_at  | DateTime  |                               |

### 3.6 AuditLog

| Column      | Type      | Notes                              |
|-------------|-----------|-------------------------------------|
| id          | UUID (PK) |                                     |
| user_id     | FK→User   |                                     |
| event_type  | String    | duress_login, panic_triggered, …    |
| detail      | JSON      |                                     |
| created_at  | DateTime  |                                     |

---

## 4. Risk Engine Design

### 4.1 Scoring Pipeline

```
Input text
    │
    ├──► URL Extractor → URLs → Safe Browsing / Mock Blocklist
    │                              │
    ├──► Language Detector         │
    │                              │
    ├──► Rules Layer ──────────────┤
    │    (per-language patterns,   │
    │     universal signals)       ▼
    │                        rule_score (0–100)
    │                        reasons[] (up to 5 raw, trimmed to 3)
    │                        advice[]
    │
    ├──► Classifier ──────────────►  classifier_score (0–100)
    │
    ▼
blended_score = RULES_WEIGHT × rule_score + CLASSIFIER_WEIGHT × classifier_score
    │
    ├── (if 30 ≤ blended_score ≤ 60 and LLM_ENABLED) ──► LLM → one-line explanation
    │
    ▼
tier = SAFE | CAUTION | HIGH_RISK  (thresholds: 0-39 / 40-69 / 70-100)
    │
    └── enforce: HIGH_RISK requires len(reasons) ≥ 1
```

### 4.2 Rule Signals and Weights

Each rule returns a `Signal(code, weight, matched)`. Weights are read from `reason_codes.json`.

| Signal Code         | Detection Logic                                      |
|---------------------|------------------------------------------------------|
| SUSPICIOUS_LINK     | URL present + Safe Browsing hit or known bad TLD     |
| REQUESTS_OTP_PIN    | Regex: asks for PIN, OTP, password, code             |
| URGENCY_LANGUAGE    | "act now", "expire", "immediately", "urgent"         |
| IMPERSONATION       | Bank/courier/govt name + mismatch patterns           |
| MOVE_TO_WHATSAPP    | "whatsapp", "wa.me", "move chat"                     |
| ASKS_FOR_MONEY      | Currency amounts + transfer verbs                    |
| FAKE_JOB_OFFER      | "hiring", "salary", "registration fee", "WFH"        |
| ADVANCE_FEE         | "release funds", "processing fee", "inheritance"     |
| ROMANCE_SCAM        | "love you", "met online", "send me"                  |
| LOOKALIKE_DOMAIN    | Edit-distance ≤ 2 from known legitimate domains      |
| SHORTENED_URL       | bit.ly, tinyurl, t.co, etc.                          |
| PHONE_IN_MESSAGE    | Embedded phone number different from sender          |
| GENERIC_GREETING    | "Dear customer", "Dear user", "Dear beneficiary"     |
| EMAIL_MISMATCH      | Sender vs reply-to domain differ                     |
| DISPLAY_NAME_SPOOF  | Display name matches known brand but domain differs  |

### 4.3 Score Blending

```python
RULES_WEIGHT    = float(os.getenv("RULES_WEIGHT", "0.6"))
CLASSIFIER_WEIGHT = float(os.getenv("CLASSIFIER_WEIGHT", "0.4"))

blended = RULES_WEIGHT * rule_score + CLASSIFIER_WEIGHT * classifier_score
blended = max(0, min(100, round(blended)))
```

### 4.4 LLM Fallback Interface

```python
# engine/llm_fallback.py
def classify_with_llm(text: str, user_lang: str) -> LLMResult | None:
    """Returns (category, explanation) or None if LLM disabled / fails."""
```

The function is a no-op when `LLM_ENABLED=false`. It wraps any LLM provider (OpenAI-compatible). The explanation is a single sentence in the user's language.

---

## 5. Transaction Rules Design

```python
# engine/transaction_rules.py
def check_transaction(proposed: ProposedTransaction, history: list[Transaction],
                       recent_scans: list[ScanResult]) -> TxnRiskResult:
```

Rules evaluate in order, each returning a `TxnSignal(code, triggered)`:

| Code                | Trigger Condition                                                   |
|---------------------|---------------------------------------------------------------------|
| NEW_RECIPIENT       | recipient not in user's last 90 days of transactions                |
| UNUSUAL_AMOUNT      | amount > 2× user's 90-day average send amount                       |
| ROUND_LARGE_AMOUNT  | amount ≥ 500 and amount % 100 == 0                                  |
| RAPID_REPEAT_SENDS  | ≥ 3 sends to same recipient in past 24 hours                        |
| AFTER_RISKY_MESSAGE | HIGH_RISK scan in past 30 minutes for this user                     |
| NEW_COUNTRY         | destination country not seen in user's history                      |

Final tier uses same thresholds as message scanning.

---

## 6. Duress and Decoy Design

### 6.1 Authentication Flow

```
POST /login  { phone, pin }
    │
    ├── verify pin_hash → normal session (is_duress=False)
    ├── verify duress_pin_hash → duress session (is_duress=True)
    │   (response shape IDENTICAL; timing equalised with constant-time compare)
    └── neither → 401 (after incrementing rate-limit counter)
```

### 6.2 Decoy Account Generator

```python
# decoy/generator.py
def generate_decoy_account(user_id: str, seed: int) -> DecoyAccount:
    rng = random.Random(seed)  # fixed seed → deterministic output
    # Generates: balance=0.00, 8-15 plausible transactions over past 120 days
    # Small amounts (R20–R200), common recipients ("Mom", "Grocery", "Airtime")
```

The seed is `hash(user_id)` so every call for the same user returns the same history.

### 6.3 Panic Button

```
POST /panic  { } (authenticated)
    │
    ├── Mark session is_duress=True
    ├── Write AuditLog(event_type="panic_triggered")
    ├── Append SMSMessage(direction="outbound", to=trusted_contact,
    │       body="[silent alert] User activated emergency mode at <timestamp>")
    └── Return { "status": "ok" }
```

---

## 7. USSD State Machine

State is encoded in the `text` parameter (inputs joined by `*`), matching Africa's Talking convention. No server-side session state is stored between USSD requests.

```
text=""           → CON: Welcome / New user? / Login
text="1"          → CON: Enter phone
text="1*+27..."   → CON: Enter PIN
text="1*+27...*1234" → CON: Main menu  (or duress menu — identical text)

Main menu:
  1 → Check a message  (CON: Paste your message)
  2 → Scam examples    (CON: List categories)
  3 → My account       (CON: Balance / last txn — shows decoy in duress)
  4 → Change language  (CON: Language list)
  5 → Exit             (END: Goodbye)
```

Responses are generated by `backend/routers/ussd.py` which calls the risk engine for option 1 and returns at most ~160 characters per screen (USSD limit).

---

## 8. API Design Summary

Full shapes are in `docs/api_contract.md`. Key endpoints:

| Method | Path                    | Auth | Description                          |
|--------|-------------------------|------|--------------------------------------|
| POST   | /register               | —    | Create account                       |
| POST   | /login                  | —    | Normal or duress login               |
| GET    | /accounts/me            | ✓    | Real or decoy account info           |
| POST   | /scan                   | opt  | Scan a message                       |
| POST   | /transactions/check     | ✓    | Pre-send risk check                  |
| POST   | /transactions/send      | ✓    | Execute send (decoy-safe)            |
| POST   | /ussd                   | —    | Africa's Talking USSD handler        |
| POST   | /sms/inbound            | —    | Receive SMS from simulator           |
| GET    | /sms/outbox             | ✓    | Fetch SMS outbox                     |
| POST   | /panic                  | ✓    | Activate panic/decoy mode            |
| POST   | /login-guard/event      | ✓    | Log dating-app event                 |
| GET    | /scams/library          | —    | Fetch scam education library         |

---

## 9. Frontend Architecture

### 9.1 Tech Stack

- React 18 + TypeScript
- Vite (dev server + build)
- Tailwind CSS (mobile-first, 320 px base)
- React Router v6 (client-side routing)
- Zustand (lightweight global state: current user, language, duress flag)
- No component library — hand-built components for full control

### 9.2 i18n Strategy

```typescript
// web/src/i18n/index.ts
const translations: Record<string, Record<string, string>> = {};

export async function loadLanguage(lang: string) {
  // Lazy-load /i18n/<lang>.json from the public folder
  translations[lang] = await fetch(`/i18n/${lang}.json`).then(r => r.json());
}

export function t(key: string, lang: string): string {
  return translations[lang]?.[key] ?? translations['en']?.[key] ?? key;
}
```

Language files are copied to `web/public/i18n/` at build time by a Vite plugin or copy step.

### 9.3 Screen Routing

```
/                   → Login
/register           → Register
/home               → Home / Dashboard
/scan               → Scanner
/send               → Send Money
/history            → Account & History
/learn              → Learn the Scams
/login-guard        → Login Guard Simulation
/ussd               → USSD Simulator
/sms                → SMS Simulator
/demo               → Demo Panel
```

### 9.4 Tier Colour and Icon System

| Tier      | Background  | Text    | Icon   | Label       |
|-----------|-------------|---------|--------|-------------|
| SAFE      | green-100   | green-800 | ✓    | "Safe"      |
| CAUTION   | yellow-100  | yellow-800 | ⚠   | "Caution"   |
| HIGH_RISK | red-100     | red-800 | ✗      | "High Risk" |

Colour is never the sole indicator — icon and text label are always present.

---

## 10. Security Design

- **PIN hashing:** bcrypt with work factor 12, or argon2id with time_cost=2, memory_cost=65536.
- **Token:** opaque UUID bearer token stored in UserSession. No JWTs for MVP simplicity.
- **Rate limiting:** `slowapi` middleware, 5 login attempts / 5 min per IP + phone.
- **Duress timing:** `secrets.compare_digest` used for both PIN comparisons; same code path to prevent timing oracle.
- **Input validation:** Pydantic v2 validators on all request bodies; max text length 10 000 chars for scan.
- **No raw message storage:** scan endpoint hashes input text (SHA-256) before storing.
- **CORS:** restricted to localhost origins in development; configured via env var for production.
- **Secrets:** all API keys in environment variables; `.env.example` documents them without values.

---

## 11. Classifier Training Design

```
data/scam_samples.json   → list of { "text": "...", "label": "scam" }
data/legit_samples.json  → list of { "text": "...", "label": "legit" }
                                    ↓
scripts/train_classifier.py:
  1. Load + combine samples
  2. TF-IDF vectoriser (max_features=5000, ngram_range=(1,2), sublinear_tf=True)
  3. LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')
  4. 5-fold cross-validation, print metrics
  5. Save Pipeline(TfidfVectorizer, LogisticRegression) → backend/model/classifier.pkl

scripts/evaluate_classifier.py:
  1. Load classifier.pkl
  2. Load legit_samples.json only
  3. Predict; count false positives (legit predicted as scam)
  4. Print: precision, recall, FP rate
```

---

## 12. Offline / Mock Strategy

| External Service       | Env Var                     | Mock Behaviour                          |
|------------------------|-----------------------------|-----------------------------------------|
| Google Safe Browsing   | `MOCK_SAFE_BROWSING=true`   | Local blocklist in `engine/url_check.py` |
| LLM (any provider)     | `LLM_ENABLED=false`         | `classify_with_llm` returns `None`      |
| Africa's Talking USSD  | N/A (simulator built-in)    | USSD simulator calls `POST /ussd`       |
| SMS gateway            | N/A (simulator built-in)    | SMS simulator reads from SQLite         |

All mocks produce identical interface shapes to the real services.

---

## 13. Demo Seed Data

`backend/seed.py` creates:
1. **Blessing** (`+27831234567`, zu, country ZA, pin `1234`, duress `9999`)
   - 12 transactions over past 90 days (ZAR, small amounts to "Mom" and "Grocery")
   - 1 HIGH_RISK scan result 10 minutes ago (fake job offer)
2. **Tendai** (`+263771234567`, en, country ZW, pin `1234`, duress `9999`)
   - 10 transactions (USD, remittances to Zimbabwe)
3. Scam library entries (5 categories × 2 examples)
4. "Scam of the Week" SMS in outbox for both users
