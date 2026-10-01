# Mukuru Detection — Implementation Tasks
> Each group ends with a summary and review step before the next group begins.

---

## Group 1 — Repo Scaffold, Shared Files, API Skeleton

**Goal:** A runnable backend returning contract-shaped mock responses, shared vocabulary files in place, and the frontend dev server rendering a blank shell.

### Task 1.1 — Create directory structure
- [ ] Create all top-level directories: `backend/`, `web/`, `ussd/`, `shared/`, `i18n/`, `data/`, `docs/`, `scripts/`
- [ ] Create `backend/engine/`, `backend/decoy/`, `backend/model/`, `backend/routers/`, `backend/schemas/`, `backend/models/`, `backend/tests/`
- [ ] Add `.gitkeep` files where needed to preserve empty dirs in git

### Task 1.2 — Shared source-of-truth files
- [ ] Create `shared/reason_codes.json` with categories, message reasons, transaction reasons, advice codes, tiers, weights, and 8 language codes (see design §4.2)
- [ ] Create `i18n/en.json` with all UI, USSD, SMS, and warning strings keyed by reason/advice codes
- [ ] Create `i18n/zu.json` as a complete isiZulu translation (same keys as `en.json`)
- [ ] Create stub draft files for `i18n/fr.json`, `sw.json`, `st.json`, `hi.json`, `nl.json`, `pt.json` with `_meta` status field and English values as placeholders

### Task 1.3 — Backend scaffold
- [ ] Create `pyproject.toml` (or `requirements.txt`) pinning: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic>=2`, `bcrypt`, `python-jose`, `slowapi`, `scikit-learn`, `langdetect`, `pytest`, `httpx`
- [ ] Create `backend/config.py` — Pydantic Settings class reading all env vars from `.env`
- [ ] Create `backend/database.py` — SQLAlchemy engine + `get_db` dependency
- [ ] Create `backend/main.py` — FastAPI app factory with CORS middleware, all routers mounted, lifespan hook that creates DB tables
- [ ] Create `backend/.env.example` documenting every env var

### Task 1.4 — Mock router stubs
- [ ] Create stub routers for every endpoint in `docs/api_contract.md`, each returning a hardcoded contract-shaped response with a `"mock": true` field
- [ ] Confirm `uvicorn backend.main:app --reload` starts without errors and every endpoint returns HTTP 200 with correct shape
- [ ] Create `docs/api_contract.md` with full endpoint definitions and JSON shapes

### Task 1.5 — Frontend scaffold
- [ ] Scaffold React + Vite + TypeScript project in `web/` using `npm create vite@latest`
- [ ] Install and configure Tailwind CSS
- [ ] Install React Router v6 and Zustand
- [ ] Create route stubs for all screens (Login, Register, Home, Scan, Send, History, Learn, Login Guard, USSD, SMS, Demo)
- [ ] Create `web/src/api/client.ts` — base fetch wrapper pointing to `http://localhost:8000`
- [ ] Confirm `npm run dev` starts without errors and the login screen renders

### Task 1.6 — Data sample files
- [ ] Create `data/scam_samples.json` with at least 60 labelled scam messages (covering all 5 categories, in English and isiZulu)
- [ ] Create `data/legit_samples.json` with at least 60 labelled legitimate messages (bank OTPs, delivery notifications, money-transfer confirmations, ordinary chats)
- [ ] Create `data/scam_library.json` with 2–3 examples per category (used by `GET /scams/library`)

**Review checkpoint:** Run `uvicorn backend.main:app` and `npm run dev`. Confirm both start, every mock endpoint returns a valid JSON shape, the React shell loads, and all 8 i18n files exist with matching keys.

---

## Group 2 — Database Models, Seed Data, Auth, Duress PIN, Decoy Account

**Goal:** Real registration, login, and duress login working end-to-end; demo users seeded; decoy account returning R0.00.

### Task 2.1 — ORM models
- [ ] Implement `backend/models/user.py` — `User` and `UserSession` tables (see design §3.1, §3.2)
- [ ] Implement `backend/models/scan.py` — `ScanResult` table
- [ ] Implement `backend/models/transaction.py` — `Transaction` table
- [ ] Implement `backend/models/sms.py` — `SMSMessage` table
- [ ] Implement `backend/models/audit.py` — `AuditLog` table
- [ ] Wire all models into `database.py` so `Base.metadata.create_all()` creates every table

### Task 2.2 — Pydantic schemas
- [ ] Create `backend/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `LoginResponse`, `AccountResponse`
- [ ] Create `backend/schemas/common.py` — `ErrorResponse`, `SuccessResponse`

### Task 2.3 — Auth router
- [ ] Implement `POST /register` — validate phone format, hash PIN and duress PIN (must differ), store user, return `LoginResponse` with token
- [ ] Implement `POST /login` — constant-time compare against both pin_hash and duress_pin_hash; set `is_duress` on session; return identical shape regardless of which PIN matched
- [ ] Implement `GET /accounts/me` — if session `is_duress`, call `decoy/generator.py`; otherwise return real account data
- [ ] Add bearer-token auth dependency used by all protected routes

### Task 2.4 — Rate limiting
- [ ] Add `slowapi` limiter to `main.py`
- [ ] Apply 5/5min limit to `POST /login` by IP + phone number

### Task 2.5 — Decoy account generator
- [ ] Implement `backend/decoy/generator.py` — fixed-seed RNG, generates balance `0.00`, 8–15 plausible transactions over past 120 days (see design §6.2)
- [ ] Unit test: call generator twice with same user_id, assert identical output

### Task 2.6 — Seed script
- [ ] Implement `backend/seed.py` — creates Blessing and Tendai, their real transaction history, one HIGH_RISK scan result (10 min ago) for Blessing, and "Scam of the Week" SMS for both
- [ ] Confirm `python backend/seed.py` runs idempotently (safe to run twice)

### Task 2.7 — Duress tests
- [ ] `tests/test_duress.py`: assert login with duress PIN returns same JSON keys as normal login
- [ ] Assert `GET /accounts/me` with duress session returns `balance: "R0.00"`
- [ ] Assert decoy history contains no real transactions
- [ ] Assert `AuditLog` entry is created on duress login

**Review checkpoint:** Register a new user, log in normally, log in with duress PIN, confirm response shapes match and `/accounts/me` shows R0.00 in duress mode. Run `pytest backend/tests/test_duress.py`.

---

## Group 3 — Risk Engine: Rules, Email Checks, URL Check, Tests

**Goal:** A fully tested pure-Python risk engine returning scores, tiers, reasons, and advice for message scans.

### Task 3.1 — Rule engine core
- [ ] Implement `backend/engine/rules.py` with all 15 signal detectors listed in design §4.2
- [ ] Each rule is a function: `def check_<name>(text: str, meta: dict) -> Signal`
- [ ] Implement aggregator: `run_rules(text, channel, meta) -> RulesResult(score, reasons, advice)`
- [ ] Reason list trimmed to top 3 by weight; advice codes derived from triggered reasons

### Task 3.2 — Language detection
- [ ] Implement `backend/engine/language_detect.py` wrapping `langdetect`, with a fallback to `"en"` on failure
- [ ] Confirm detection works on isiZulu sample text

### Task 3.3 — Keyword lists
- [ ] Add complete English keyword/pattern lists to `rules.py` covering all 5 categories
- [ ] Add complete isiZulu keyword/pattern lists (coordinate with `i18n/zu.json` vocabulary)
- [ ] Add shorter lists for `fr`, `sw`, `st`, `hi`, `nl`, `pt`

### Task 3.4 — Email checks
- [ ] Implement `backend/engine/email_checks.py` with checks for: sender/reply-to mismatch, display-name spoof, generic greeting, lookalike domain, urgent subject
- [ ] Wire email checks into `run_rules` when `channel == "email"`

### Task 3.5 — URL check
- [ ] Implement `backend/engine/url_check.py` — extract URLs with regex, then:
  - Mock mode (default): check against local blocklist of 20+ known bad domains
  - Live mode: call Google Safe Browsing Lookup API v4 with the extracted URLs only
- [ ] Env vars: `MOCK_SAFE_BROWSING=true` (default), `SAFE_BROWSING_API_KEY`
- [ ] Return `UrlCheckResult(urls_found, any_malicious, source)`

### Task 3.6 — Scan router (real implementation)
- [ ] Replace stub `POST /scan` with real implementation calling `run_rules`
- [ ] Store `ScanResult` in DB (hash the text, never store raw)
- [ ] Record `ScanResult` on the user's risk state (for `AFTER_RISKY_MESSAGE` later)

### Task 3.7 — Rules tests
- [ ] `tests/test_rules.py`: one test per signal type with a positive and negative example
- [ ] Test that HIGH_RISK never returns without reasons
- [ ] Test fake-job-offer sample from demo story → HIGH_RISK, category `fake_job_offer`
- [ ] Test bank OTP sample → SAFE or CAUTION, no `FAKE_JOB_OFFER` reason

**Review checkpoint:** `pytest backend/tests/test_rules.py` all pass. Run the demo fake-job SMS through `POST /scan` and confirm tier=HIGH_RISK, ≥1 reason, ≤3 reasons.

---

## Group 4 — Classifier, Score Blending, Evaluation, LLM Fallback

**Goal:** Trained classifier blended with rules, evaluation script showing FP rate, optional LLM fallback wired in.

### Task 4.1 — Training script
- [ ] Implement `scripts/train_classifier.py`:
  - Load `data/scam_samples.json` + `data/legit_samples.json`
  - Build `Pipeline(TfidfVectorizer(max_features=5000, ngram_range=(1,2), sublinear_tf=True), LogisticRegression(class_weight='balanced'))`
  - 5-fold CV, print metrics
  - Save to `backend/model/classifier.pkl`
- [ ] Run the script and commit the trained model artifact

### Task 4.2 — Classifier module
- [ ] Implement `backend/engine/classifier.py`:
  - Load `classifier.pkl` once at import time (lazy load with `functools.lru_cache`)
  - `predict(text: str) -> float` — returns probability (0.0–1.0) of scam
  - Graceful degradation: if model file missing, log warning and return 0.5

### Task 4.3 — Score blending
- [ ] Update `POST /scan` pipeline to call both `run_rules` and `classifier.predict`
- [ ] Apply blend formula: `RULES_WEIGHT * rules_score + CLASSIFIER_WEIGHT * classifier_score`
- [ ] Read weights from env vars with defaults 0.6 / 0.4
- [ ] Enforce: blended HIGH_RISK still requires at least one reason from rules

### Task 4.4 — LLM fallback
- [ ] Implement `backend/engine/llm_fallback.py` — calls any OpenAI-compatible API
- [ ] Trigger only when `30 ≤ blended_score ≤ 60` and `LLM_ENABLED=true`
- [ ] Return `LLMResult(category, explanation)` or `None`
- [ ] Set `explanation_source="llm"` in the scan response when used
- [ ] Test: with `LLM_ENABLED=false`, confirm no LLM call is made and app still works

### Task 4.5 — Evaluation script
- [ ] Implement `scripts/evaluate_classifier.py`:
  - Load model, run on legit samples only
  - Print: precision, recall, false-positive rate
  - Exit with code 1 if FP rate > 10%
- [ ] Run and record the baseline FP rate in `docs/README.md`

**Review checkpoint:** Run `python scripts/evaluate_classifier.py` and confirm FP rate ≤ 10%. Rescan demo fake-job SMS and confirm score is still HIGH_RISK with blending active.

---

## Group 5 — Transaction Rules, Endpoints, Risk State

**Goal:** Transaction pre-send check working end-to-end, wired to scan risk state, with "Send anyway / Pause" UI flow.

### Task 5.1 — Transaction rules engine
- [ ] Implement `backend/engine/transaction_rules.py` with all 6 rules (design §5)
- [ ] `check_transaction(proposed, history, recent_scans) -> TxnRiskResult`
- [ ] `AFTER_RISKY_MESSAGE`: query `ScanResult` for user in past 30 min with tier=HIGH_RISK

### Task 5.2 — Transaction schemas
- [ ] Create `backend/schemas/transaction.py` — `TransactionCheckRequest`, `TransactionCheckResponse`, `SendRequest`, `SendResponse`

### Task 5.3 — Transaction router
- [ ] Implement `POST /transactions/check` — run `check_transaction`, return result
- [ ] Implement `POST /transactions/send`:
  - Call `check_transaction` first; if HIGH_RISK and no `force=true`, return 422 with reasons
  - If `force=true` or SAFE/CAUTION: in duress mode write decoy Transaction; otherwise write real Transaction
- [ ] Implement `GET /transactions/history` — return real or decoy history based on session

### Task 5.4 — Transaction rules tests
- [ ] `tests/test_transaction_rules.py`:
  - Test `AFTER_RISKY_MESSAGE` triggers when HIGH_RISK scan exists in past 30 min
  - Test `NEW_RECIPIENT` triggers for unknown recipient
  - Test `UNUSUAL_AMOUNT` triggers at 2× average
  - Test in duress mode: send writes decoy record, real balance unchanged

### Task 5.5 — Send Money screen (web)
- [ ] Build `/send` screen: recipient, amount, currency fields
- [ ] On submit: call `POST /transactions/check`; if CAUTION/HIGH_RISK show warning card with reasons and "Pause / Send anyway" buttons
- [ ] "Send anyway" sets `force=true` and calls `POST /transactions/send`

**Review checkpoint:** With Blessing's seeded HIGH_RISK scan active, submit a send to a new recipient and confirm `AFTER_RISKY_MESSAGE` + `NEW_RECIPIENT` appear in the warning. Run `pytest backend/tests/test_transaction_rules.py`.

---

## Group 6 — USSD Endpoint, USSD Simulator, SMS Endpoints, SMS Simulator

**Goal:** Phone-shaped USSD and SMS simulators working in the browser, backed by real endpoints.

### Task 6.1 — USSD router
- [ ] Implement `POST /ussd` state machine (design §7) — stateless, all state in the `text` parameter
- [ ] Flows: new user registration (country → language → PIN → duress PIN → confirm), login, main menu (check message, scam examples, my account, change language, exit)
- [ ] Scam-check flow: accept pasted message text, run `POST /scan`, return tier + top reason in ≤160 chars
- [ ] All strings looked up from `i18n/<lang>.json` via reason/advice codes
- [ ] Language stored on User; changeable from menu option 4

### Task 6.2 — USSD simulator (web)
- [ ] Build `/ussd` screen: phone-shaped frame, digit keypad, scrollable display area
- [ ] Input box accepts `*` separated entries; on submit sends `POST /ussd` with accumulated `text`
- [ ] Parse `CON` (show input) vs `END` (show final message, hide input) prefix
- [ ] Show "Demo" shortcuts: Blessing's number / Tendai's number pre-filled

### Task 6.3 — SMS router
- [ ] Implement `POST /sms/inbound` — accept `{ from, body }`; parse command (e.g. "1" = check last scan result) and append reply to outbox
- [ ] Implement `GET /sms/outbox` — return user's SMSMessage list
- [ ] Send-scan-result-by-SMS helper: format result ≤160 chars (or shorter for Hindi)

### Task 6.4 — SMS simulator (web)
- [ ] Build `/sms` screen: phone-shaped inbox list + compose box
- [ ] Poll `GET /sms/outbox` on load; display messages as chat bubbles (outbound right, inbound left)
- [ ] Compose box calls `POST /sms/inbound`

### Task 6.5 — Scam of the Week
- [ ] `seed.py` appends a "Scam of the Week" message to each demo user's outbox in their language
- [ ] Message contains a real example scam snippet and a 1-sentence red-flag explanation ≤160 chars

**Review checkpoint:** Open USSD simulator, register a new user in isiZulu, check a scam message via the menu, and confirm the risk result appears. Open SMS simulator, confirm "Scam of the Week" is in the outbox.

---

## Group 7 — Web App Screens, i18n Wiring, English and isiZulu Complete

**Goal:** All screens built, language switcher working, English and isiZulu fully translated throughout the UI.

### Task 7.1 — Auth screens
- [ ] Build `/login` screen — phone + PIN fields, "Demo login" shortcuts, language selector
- [ ] Build `/register` screen — phone, PIN, duress PIN, country selector, language selector
- [ ] Wire to `POST /login` and `POST /register`; store token in Zustand + localStorage

### Task 7.2 — Scanner screen
- [ ] Build `/scan` screen — textarea for message text, channel selector (web/email/sms), submit button
- [ ] On result: show `ResultCard` component (tier colour + icon + label, score, ≤3 reasons, advice)
- [ ] Reasons and advice rendered using `t(code, lang)` from i18n

### Task 7.3 — Result card component
- [ ] `ResultCard` props: `{ tier, score, category, reasons[], advice[], explanationSource }`
- [ ] Three tiers: SAFE (green), CAUTION (yellow), HIGH_RISK (red) — always includes text label and icon, never colour alone
- [ ] Advice rendered as actionable one-line instructions

### Task 7.4 — Account and history screen
- [ ] Build `/history` screen — balance, last 10 transactions
- [ ] In duress mode: shows R0.00 and decoy history (no visible difference in layout)

### Task 7.5 — Language switcher
- [ ] Language switcher component (dropdown) in the app header
- [ ] On change: update Zustand language state, reload i18n translations, call `PATCH /accounts/me` to persist language preference
- [ ] Add `PATCH /accounts/me` endpoint (language field only)

### Task 7.6 — i18n completeness
- [ ] Complete all strings in `i18n/en.json` — every UI label, USSD screen, SMS template, tier label, reason text, advice text
- [ ] Complete all strings in `i18n/zu.json` — full isiZulu translation
- [ ] Confirm i18n key parity test passes: `pytest backend/tests/test_i18n_parity.py`

### Task 7.7 — Demo panel
- [ ] Build `/demo` screen — seeded user credentials, one-click "load sample scam" buttons per category, one-click "log in as Blessing/Tendai" shortcuts
- [ ] Sample scam messages auto-populate the scanner textarea on click

**Review checkpoint:** Switch language to isiZulu; confirm Login, Scanner, and Result Card all render in isiZulu. Run the demo story manually: login as Blessing → scan fake-job SMS → confirm HIGH_RISK card in isiZulu.

---

## Group 8 — Login Guard, Panic Flow, Learning Library

**Goal:** Panic button, duress UX, Login Guard simulation, and Learn the Scams screen all functional.

### Task 8.1 — Panic button
- [ ] Add "Emergency" button to the header/home screen (low-key label, e.g. "Safety options")
- [ ] Button navigates to a confirmation screen that clearly explains what will happen
- [ ] On confirm: call `POST /panic`, switch Zustand to duress mode, redirect to `/history` (now showing decoy)
- [ ] `POST /panic` router: mark session `is_duress=True`, write `AuditLog`, send silent SMS to trusted contact

### Task 8.2 — Duress UI consistency
- [ ] Confirm that after panic: header, nav, and all screens look identical to normal mode
- [ ] Confirm Send Money in duress mode: UI shows success, DB writes decoy record, real balance unchanged

### Task 8.3 — Login Guard
- [ ] Build `/login-guard` screen — "Simulate dating-app login" button, clear simulation label
- [ ] On button click: show check-in question ("Has someone you met online asked you for money?")
- [ ] "Yes" answer: call `POST /login-guard/event`, show romance-scam advice card, update user risk state
- [ ] `POST /login-guard/event` router: set a `login_guard_alert` flag on the user record; this flag feeds `AFTER_RISKY_MESSAGE` for 60 minutes

### Task 8.4 — Learning library screen
- [ ] Implement `GET /scams/library?lang=` router — load from `data/scam_library.json`, return entries with translated reason text
- [ ] Build `/learn` screen — accordion or card list grouped by category, showing example message + red-flag reasons + advice

**Review checkpoint:** Click panic button, confirm UI shows R0.00 with no visible mode change. Activate Login Guard, answer "yes", send money — confirm `AFTER_RISKY_MESSAGE` triggers even without a prior scan.

---

## Group 9 — Draft Languages, Key-Parity Tests

**Goal:** Six draft language files complete enough for a demo, key-parity test enforced in CI.

### Task 9.1 — Draft language files
- [ ] Complete `i18n/fr.json` — French translations for all keys; add `_meta` draft status
- [ ] Complete `i18n/sw.json` — Swahili translations; add `_meta`
- [ ] Complete `i18n/st.json` — Sesotho translations; add `_meta`
- [ ] Complete `i18n/hi.json` — Hindi translations + romanised Latin fallback for all USSD/SMS keys; add `_meta`
- [ ] Complete `i18n/nl.json` — Dutch translations; add `_meta`
- [ ] Complete `i18n/pt.json` — Portuguese (Mozambican phrasing where it differs); add `_meta`

### Task 9.2 — Key-parity test
- [ ] Implement `backend/tests/test_i18n_parity.py`:
  - Load `i18n/en.json` as the reference key set
  - For each of the 7 other language files: assert every key present in `en.json` is also present in the file
  - Fail with a clear message listing missing keys per language
- [ ] All 8 language files pass the parity test

### Task 9.3 — Language demo in web app
- [ ] Confirm the language switcher cycles through all 8 languages and the scanner result card re-renders in each
- [ ] Show a quick language cycle in the demo panel (one-click "show result in all languages")

**Review checkpoint:** `pytest backend/tests/test_i18n_parity.py` passes. Demo panel language cycle works.

---

## Group 10 — End-to-End Demo Test, README, Demo Script

**Goal:** Automated proof that the demo story runs; clear README and demo script ready for judges.

### Task 10.1 — End-to-end test
- [ ] Implement `backend/tests/test_e2e_demo.py` using `httpx.AsyncClient` against a test database:
  1. Register a new user (isiZulu)
  2. `POST /scan` with the fake-job SMS → assert tier=HIGH_RISK, category=fake_job_offer
  3. `POST /transactions/check` to new recipient → assert `AFTER_RISKY_MESSAGE` + `NEW_RECIPIENT` in reasons
  4. `POST /login` with duress PIN → assert response shape identical to normal login
  5. `GET /accounts/me` → assert balance=R0.00
  6. `POST /transactions/send` in duress session → assert HTTP 200, real balance unchanged
- [ ] All 6 assertions pass

### Task 10.2 — README
- [ ] Write `docs/README.md` covering:
  - Project overview and demo story (Blessing)
  - Prerequisites (Python 3.11, Node 18+)
  - Quick start: 3 commands (seed, backend, frontend)
  - Environment variables (reference `.env.example`)
  - Running tests: `pytest` and `npm test`
  - Running evaluation: `python scripts/evaluate_classifier.py`
  - Recorded FP rate from Task 4.5
  - Architecture summary (2 paragraphs)
  - Out-of-scope notice

### Task 10.3 — Demo script
- [ ] Write `docs/demo_script.md` — step-by-step 5-minute judge walkthrough:
  1. Open demo panel, log in as Blessing (isiZulu)
  2. USSD simulator: check the pre-loaded fake-job SMS
  3. Scanner screen: confirm HIGH_RISK card in isiZulu with reasons
  4. Send Money: trigger `AFTER_RISKY_MESSAGE` warning
  5. Language switcher: cycle to English, confirm same result
  6. Panic button: show R0.00, send money, show no real change
  7. SMS simulator: show "Scam of the Week"
  8. Learn the Scams: browse library
  9. Login Guard: activate, answer yes, trigger romance-scam advice
  10. Run `python scripts/evaluate_classifier.py` live, show FP rate

### Task 10.4 — Final cleanup
- [ ] Confirm `.gitignore` excludes: `*.pkl`, `*.db`, `.env`, `__pycache__/`, `node_modules/`, `dist/`
- [ ] Confirm `.env.example` documents every env var used in the codebase
- [ ] Remove all `"mock": true` fields from production responses
- [ ] Run full `pytest` suite — all tests pass
- [ ] Run `npm run build` — no TypeScript or Vite errors

**Review checkpoint:** `pytest` green. `python scripts/evaluate_classifier.py` prints FP rate ≤ 10%. Full demo story walkable in under 5 minutes using `docs/demo_script.md`.

---

## Acceptance Criteria Checklist

- [ ] New user signs up in isiZulu via USSD in under 1 minute
- [ ] Sample fake-job SMS scores HIGH_RISK with reasons and advice shown in isiZulu
- [ ] Send to new recipient after that scan is flagged with `AFTER_RISKY_MESSAGE`
- [ ] Duress PIN login shows R0.00 and plausible history; a send does not change the real balance
- [ ] Same scan result displayable in all 8 languages via language switcher
- [ ] Evaluation script shows false-positive rate ≤ 10%
