# Mukuru Detection — Requirements
> Format: EARS (Easy Approach to Requirements Syntax)
> Version: 1.0 | Hackathon MVP

---

## 1. Accounts, USSD and Mock Logins

### 1.1 Registration
- **REQ-1.1.1** The system shall allow a user to register with a phone number, a 4-digit PIN, and a separate 4-digit duress PIN.
- **REQ-1.1.2** The system shall hash all PINs using bcrypt or argon2 before storage; plain-text PINs shall never be persisted.
- **REQ-1.1.3** The system shall reject registration if the PIN and duress PIN are identical.
- **REQ-1.1.4** The system shall require the user to select a country during registration, and shall pre-select a default language based on that country.
- **REQ-1.1.5** The system shall allow the user to override the pre-selected language at registration time and at any point thereafter.

### 1.2 Login
- **REQ-1.2.1** The system shall authenticate a user by phone number and PIN.
- **REQ-1.2.2** When a user provides the duress PIN, the system shall return a response that is identical in JSON shape and timing to a normal-login response.
- **REQ-1.2.3** The system shall apply rate limiting to login attempts (maximum 5 attempts per phone number per 5-minute window) and return HTTP 429 on excess attempts.

### 1.3 USSD Simulator
- **REQ-1.3.1** The system shall expose a `POST /ussd` endpoint that accepts Africa's Talking-style session parameters (`sessionId`, `serviceCode`, `phoneNumber`, `text`) and returns a `CON` or `END` prefixed string.
- **REQ-1.3.2** The USSD sign-up flow shall proceed in this order: (1) choose country, (2) choose language, (3) set PIN, (4) set duress PIN, (5) confirm registration.
- **REQ-1.3.3** The USSD main menu shall offer: (1) Check a message, (2) Scam examples, (3) My account, (4) Change language, (5) Exit.
- **REQ-1.3.4** The web app shall include a phone-shaped USSD simulator UI that sends inputs to `POST /ussd` and displays the CON/END responses exactly as a feature phone would.
- **REQ-1.3.5** The USSD simulator shall support entering a duress PIN at the login step, with no visible difference in the displayed response.

### 1.4 Mock Logins and Demo Panel
- **REQ-1.4.1** The system shall seed two demo users: one South African (Blessing, phone `+27831234567`, language `zu`) and one Zimbabwean (Tendai, phone `+263771234567`, language `en`).
- **REQ-1.4.2** The web app shall display a "Demo" panel listing seeded user credentials and one-click sample scam messages for use in a live demo.

---

## 2. Message and Email Scam Detection

### 2.1 Scan Endpoint
- **REQ-2.1.1** The system shall expose `POST /scan` that accepts `text`, `channel` (`web | ussd | sms | email`), and optional `user_id`.
- **REQ-2.1.2** `POST /scan` shall return `score` (0–100), `tier` (`SAFE | CAUTION | HIGH_RISK`), `category`, up to 3 `reasons` (reason codes from `reason_codes.json`), `advice` codes, and `explanation_source`.
- **REQ-2.1.3** The system shall never return `HIGH_RISK` without at least one reason code.
- **REQ-2.1.4** Tier thresholds shall be: SAFE = 0–39, CAUTION = 40–69, HIGH_RISK = 70–100.

### 2.2 Rules Layer
- **REQ-2.2.1** The rules layer shall detect language-independent signals: external links, lookalike or shortened domains, OTP/PIN requests, phone numbers embedded in text, monetary amounts, and "move to WhatsApp" phrases.
- **REQ-2.2.2** The rules layer shall include complete keyword and pattern lists for English and isiZulu, and shorter lists for French, Swahili, Sesotho, Hindi, Dutch, and Portuguese.
- **REQ-2.2.3** Each rule shall produce a weighted score contribution and map to at least one reason code from `reason_codes.json`.

### 2.3 Email-Specific Checks
- **REQ-2.3.1** When `channel` is `email`, the system shall check for: sender vs reply-to address mismatch, display-name vs domain mismatch, generic greetings, lookalike domains, and urgent subject-line patterns.
- **REQ-2.3.2** Email-specific signals shall map to existing reason codes.

### 2.4 URL Check
- **REQ-2.4.1** The system shall extract all URLs from scanned text and check them for known malicious indicators.
- **REQ-2.4.2** When `SAFE_BROWSING_API_KEY` is set in the environment, the system shall call the Google Safe Browsing Lookup API and add the result as an input signal for `SUSPICIOUS_LINK`.
- **REQ-2.4.3** When `SAFE_BROWSING_API_KEY` is not set or `MOCK_SAFE_BROWSING=true`, the system shall use a local blocklist and return identical signal shapes (mock mode shall be the default so the demo works offline).
- **REQ-2.4.4** The system shall send only URLs to Google Safe Browsing; message text shall never be sent.

### 2.5 Scam Categories
- **REQ-2.5.1** The system shall detect the following categories: `phishing`, `romance_scam`, `fake_job_offer`, `advance_fee`, `impersonation`.

---

## 3. AI Classifier

### 3.1 Model
- **REQ-3.1.1** The system shall include a scikit-learn TF-IDF + logistic regression classifier trained on `data/scam_samples.json` and `data/legit_samples.json`.
- **REQ-3.1.2** A `scripts/train_classifier.py` script shall retrain the model and save it as `backend/model/classifier.pkl`.
- **REQ-3.1.3** Final score shall be blended: `0.6 × rules_score + 0.4 × classifier_score`. Blend weights shall be configurable via environment variables `RULES_WEIGHT` and `CLASSIFIER_WEIGHT`.

### 3.2 Reason Ownership
- **REQ-3.2.1** Reasons and advice codes shall always come from the rules layer. The classifier shall adjust the numeric score only; it shall not add or remove reason codes.

### 3.3 LLM Fallback
- **REQ-3.3.1** When the blended score is between 30 and 60 (inclusive) or the message is in a language with weak rule coverage, the system may optionally call a configured LLM to classify the message and generate a one-line explanation.
- **REQ-3.3.2** When the LLM is used, `explanation_source` shall be set to `"llm"`.
- **REQ-3.3.3** Setting `LLM_ENABLED=false` (the default) shall fully disable LLM calls; the system shall operate without them.

### 3.4 Evaluation
- **REQ-3.4.1** A `scripts/evaluate_classifier.py` script shall print precision, recall, and false-positive rate on the legitimate sample set.
- **REQ-3.4.2** The legitimate sample set shall include bank OTPs, genuine delivery notifications, money-transfer confirmations, and ordinary chat messages.

---

## 4. Transaction Monitoring

### 4.1 Pre-Send Check
- **REQ-4.1.1** The system shall expose `POST /transactions/check` that evaluates a proposed send against the user's history and returns `score`, `tier`, `reasons`, and `advice`.
- **REQ-4.1.2** Transaction rules shall include: `NEW_RECIPIENT`, `UNUSUAL_AMOUNT`, `ROUND_LARGE_AMOUNT`, `RAPID_REPEAT_SENDS`, `AFTER_RISKY_MESSAGE`, `NEW_COUNTRY`.
- **REQ-4.1.3** `AFTER_RISKY_MESSAGE` shall trigger when a `HIGH_RISK` scan exists for the user in the past 30 minutes.

### 4.2 Send Flow
- **REQ-4.2.1** The web app "Send Money" screen shall call `POST /transactions/check` before confirming any send.
- **REQ-4.2.2** When the check returns `CAUTION` or `HIGH_RISK`, the UI shall show reasons and a "Pause / Send anyway" choice.
- **REQ-4.2.3** In duress mode, all send attempts shall return a success response to the UI but shall write only to the decoy account; no real balance shall change.

### 4.3 Seed Data
- **REQ-4.3.1** The system shall seed realistic transaction history (at least 10 transactions per demo user, spread over the past 3 months) to enable `UNUSUAL_AMOUNT`, `NEW_RECIPIENT`, and `AFTER_RISKY_MESSAGE` detection in the demo.

---

## 5. Duress Login and Panic Button

### 5.1 Duress Mode
- **REQ-5.1.1** When a user authenticates with the duress PIN, `GET /accounts/me` shall return a decoy account with balance `R0.00` and a believable transaction history generated from a fixed seed per user.
- **REQ-5.1.2** The decoy history shall consist of small everyday sends and receives spread over the past months, and shall be identical every time it is generated for the same user.
- **REQ-5.1.3** Nothing in the UI, USSD text, or API response shall reveal that duress mode is active.
- **REQ-5.1.4** Every duress session event shall be logged for later audit.

### 5.2 Panic Button
- **REQ-5.2.1** The web app shall include an "Emergency" button that, when activated, calls `POST /panic` and switches the current session to duress/decoy view.
- **REQ-5.2.2** The panic button label on the main screen shall not use alarming words visible at a glance; the confirmation screen behind it may describe the action more clearly.
- **REQ-5.2.3** When panic is triggered, the system shall write a silent alert to the user's trusted contact's simulated SMS outbox.

---

## 6. Dating-App Login Guard (Mock)

- **REQ-6.1.1** The web app shall include a clearly labelled "Simulate dating-app login" button.
- **REQ-6.1.2** `POST /login-guard/event` shall accept a `user_id` and `event_type`, and return a check-in question ("Has someone you met online asked you for money?").
- **REQ-6.1.3** When the user answers "yes", the system shall return romance-scam advice and shall raise the user's risk state so that subsequent `AFTER_RISKY_MESSAGE` checks are affected.
- **REQ-6.1.4** The UI shall clearly communicate that this feature is a simulation.

---

## 7. Feature-Phone SMS Experience

- **REQ-7.1.1** The web app shall include a phone-shaped SMS simulator showing the user's SMS outbox via `GET /sms/outbox`.
- **REQ-7.1.2** The SMS simulator shall allow the user to send a text to the service via `POST /sms/inbound` (for example, replying `1` to trigger a message check).
- **REQ-7.1.3** The system shall send a "Scam of the Week" message to the user's outbox in their chosen language, containing a real example scam message and a short explanation of the red flags.
- **REQ-7.1.4** Scan results returned by SMS shall be limited to approximately 160 characters for Latin-script languages; Hindi messages shall use a shorter limit to account for UCS-2 encoding.

---

## 8. Languages

- **REQ-8.1.1** The system shall support eight language codes: `en`, `zu`, `fr`, `sw`, `st`, `hi`, `nl`, `pt`.
- **REQ-8.1.2** API responses shall return codes only; all human-readable strings shall come from `i18n/<lang>.json`.
- **REQ-8.1.3** `i18n/en.json` and `i18n/zu.json` shall be complete (every key present and translated).
- **REQ-8.1.4** `i18n/fr.json`, `i18n/sw.json`, `i18n/st.json`, `i18n/hi.json`, `i18n/nl.json`, and `i18n/pt.json` shall be present as drafts and shall include `"_meta": {"status": "draft, needs native review"}`.
- **REQ-8.1.5** A pytest test shall fail if any language file is missing a key present in `en.json`.
- **REQ-8.1.6** `i18n/hi.json` shall include a romanised Latin-script fallback for every USSD and SMS string.
- **REQ-8.1.7** The system shall detect the language of the scanned message independently of the user's chosen language, and shall still explain findings in the user's language.

---

## 9. Learning Library

- **REQ-9.1.1** `GET /scams/library` shall accept a `lang` query parameter and return 2–3 example scams per category.
- **REQ-9.1.2** Each library entry shall include the category, a short example message, and the red-flag reason codes.
- **REQ-9.1.3** The web app shall include a "Learn the Scams" screen that renders library entries.

---

## 10. Web App Screens

- **REQ-10.1.1** The web app shall include: Login, Register, Language Switcher, Scanner (paste message or email), Result Card, Send Money, Account & History, Learn the Scams, Login Guard Simulation, Panic Button, USSD Simulator, SMS Simulator, and Demo Panel.
- **REQ-10.1.2** The Result Card shall display tier colour **and** a text label or icon (not colour alone) for accessibility (WCAG 1.4.1).
- **REQ-10.1.3** At most 3 reasons shall be displayed per result, each in plain language with one clear next step.
- **REQ-10.1.4** The app shall be mobile-first and responsive (usable on a 320 px viewport).

---

## 11. Non-Functional Requirements

- **REQ-11.1.1** The system shall start with two commands: `uvicorn` for the backend and `npm run dev` for the frontend.
- **REQ-11.1.2** A single `python backend/seed.py` command shall seed all demo data.
- **REQ-11.1.3** The system shall operate fully offline for the demo (Safe Browsing and LLM calls are optional and mockable).
- **REQ-11.1.4** All secrets shall be read from environment variables; no secrets shall be committed to the repo. A `.env.example` shall document all variables.
- **REQ-11.1.5** The backend and frontend shall communicate only through the documented API; no shared module imports across the boundary.
- **REQ-11.1.6** The risk engine shall be a pure Python module with no FastAPI or web framework imports.
- **REQ-11.1.7** The false-positive rate on legitimate messages, as reported by the evaluation script, shall be minimised; a result above 10 % shall be considered a quality failure.

---

## 12. Testing

- **REQ-12.1.1** pytest shall cover: risk engine rules, transaction rules, duress mode (identical response shape, decoy data, no real transfer), and i18n key parity.
- **REQ-12.1.2** A small end-to-end test shall exercise the full demo story: register → scan scam message → check transaction → duress login → verify decoy balance.

---

## Out of Scope

- Real telecom or USSD integration
- Real money movement
- Real call interception
- Authentication beyond PIN
- Production deployment
- Native mobile apps
