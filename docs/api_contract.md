# Mukuru Detection — API Contract
> Version: 1.0 | Base URL: `http://localhost:8000`
> All requests and responses use `application/json`.
> Protected endpoints require `Authorization: Bearer <token>`.

---

## Authentication

### POST /register

Create a new user account.

**Request**
```json
{
  "phone": "+27831234567",
  "country": "ZA",
  "language": "zu",
  "pin": "1234",
  "duress_pin": "9999",
  "trusted_contact": "+27821234567"
}
```

**Constraints**
- `phone`: E.164 format, required
- `pin` / `duress_pin`: exactly 4 digits, must differ from each other
- `language`: one of `en | zu | fr | sw | st | hi | nl | pt`
- `country`: ISO 3166-1 alpha-2
- `trusted_contact`: optional, E.164 format

**Response 201**
```json
{
  "token": "uuid-bearer-token",
  "user": {
    "id": "uuid",
    "phone": "+27831234567",
    "country": "ZA",
    "language": "zu",
    "created_at": "2026-10-01T10:00:00Z"
  }
}
```

**Errors**
- `400` — validation failure (body contains `field` and `message`)
- `409` — phone number already registered

---

### POST /login

Authenticate with phone + PIN. Works for both the main PIN and the duress PIN.
The response shape is **identical** regardless of which PIN was used.
The `is_duress` field is intentionally omitted from the response.

**Request**
```json
{
  "phone": "+27831234567",
  "pin": "1234"
}
```

**Response 200**
```json
{
  "token": "uuid-bearer-token",
  "user": {
    "id": "uuid",
    "phone": "+27831234567",
    "country": "ZA",
    "language": "zu",
    "created_at": "2026-10-01T10:00:00Z"
  }
}
```

**Errors**
- `401` — incorrect phone or PIN
- `429` — rate limit exceeded (5 attempts / 5 min)

---

### GET /accounts/me

Return the authenticated user's account data.
In duress mode, returns decoy data (balance `R0.00`, synthetic history).
The response shape is **identical** in both modes.

**Headers:** `Authorization: Bearer <token>`

**Response 200**
```json
{
  "id": "uuid",
  "phone": "+27831234567",
  "country": "ZA",
  "language": "zu",
  "balance": "0.00",
  "currency": "ZAR",
  "recent_transactions": [
    {
      "id": "uuid",
      "recipient": "Mom",
      "amount": "50.00",
      "currency": "ZAR",
      "direction": "sent",
      "created_at": "2026-09-28T14:22:00Z"
    }
  ],
  "created_at": "2026-10-01T10:00:00Z"
}
```

**Errors**
- `401` — missing or invalid token

---

### PATCH /accounts/me

Update language preference.

**Headers:** `Authorization: Bearer <token>`

**Request**
```json
{
  "language": "en"
}
```

**Response 200**
```json
{
  "language": "en"
}
```

**Errors**
- `400` — unsupported language code
- `401` — missing or invalid token

---

## Scanning

### POST /scan

Scan a message or email for scam signals.

**Headers:** `Authorization: Bearer <token>` (optional — anonymous scans allowed)

**Request**
```json
{
  "text": "Congratulations! You have been selected for a work-from-home job...",
  "channel": "sms",
  "user_id": "uuid"
}
```

**Constraints**
- `text`: 1–10 000 characters, required
- `channel`: one of `web | ussd | sms | email`, required
- `user_id`: optional; links the scan to the user's risk state (used by `AFTER_RISKY_MESSAGE`)

**Response 200**
```json
{
  "id": "uuid",
  "score": 85,
  "tier": "HIGH_RISK",
  "category": "fake_job_offer",
  "reasons": [
    "FAKE_JOB_OFFER",
    "ASKS_FOR_MONEY",
    "MOVE_TO_WHATSAPP"
  ],
  "advice": [
    "DO_NOT_PAY_UPFRONT",
    "VERIFY_SENDER",
    "REPORT_SCAM"
  ],
  "explanation": "This message asks for an upfront registration fee, which is a classic fake job offer pattern.",
  "explanation_source": "rules",
  "detected_language": "en",
  "scanned_at": "2026-10-01T10:05:00Z"
}
```

**Notes**
- `reasons`: array of 1–3 reason codes from `shared/reason_codes.json`
- `advice`: array of 1–3 advice codes from `shared/reason_codes.json`
- `tier` is `HIGH_RISK` only when `len(reasons) >= 1`
- `explanation_source`: `"rules"` or `"llm"`

**Errors**
- `400` — validation failure
- `422` — text is empty or channel is invalid

---

## Transactions

### POST /transactions/check

Run a pre-send risk check. Does not execute the transfer.

**Headers:** `Authorization: Bearer <token>`

**Request**
```json
{
  "recipient": "+263771234567",
  "amount": "500.00",
  "currency": "ZAR",
  "country": "ZW"
}
```

**Response 200**
```json
{
  "score": 65,
  "tier": "CAUTION",
  "reasons": [
    "AFTER_RISKY_MESSAGE",
    "NEW_RECIPIENT"
  ],
  "advice": [
    "PAUSE_AND_CONFIRM",
    "DO_NOT_PAY_UPFRONT"
  ],
  "checked_at": "2026-10-01T10:06:00Z"
}
```

**Errors**
- `400` — validation failure
- `401` — missing or invalid token

---

### POST /transactions/send

Execute a money transfer. Calls the risk check internally.
In duress mode, returns a success response but writes only a decoy record.

**Headers:** `Authorization: Bearer <token>`

**Request**
```json
{
  "recipient": "+263771234567",
  "amount": "500.00",
  "currency": "ZAR",
  "country": "ZW",
  "force": false
}
```

**Constraints**
- `force`: if `true`, proceeds even when tier is `HIGH_RISK`

**Response 200**
```json
{
  "transaction_id": "uuid",
  "status": "completed",
  "amount": "500.00",
  "currency": "ZAR",
  "recipient": "+263771234567",
  "sent_at": "2026-10-01T10:06:30Z"
}
```

**Response 422** (when tier is HIGH_RISK and `force` is `false`)
```json
{
  "error": "high_risk_transfer_blocked",
  "score": 80,
  "tier": "HIGH_RISK",
  "reasons": ["AFTER_RISKY_MESSAGE", "NEW_RECIPIENT"],
  "advice": ["PAUSE_AND_CONFIRM"]
}
```

**Errors**
- `401` — missing or invalid token
- `422` — high risk and force not set

---

### GET /transactions/history

Return the user's transaction history.
In duress mode, returns the decoy history.

**Headers:** `Authorization: Bearer <token>`

**Query params:** `limit` (default 20), `offset` (default 0)

**Response 200**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "recipient": "Mom",
      "amount": "50.00",
      "currency": "ZAR",
      "direction": "sent",
      "country": "ZW",
      "status": "completed",
      "created_at": "2026-09-28T14:22:00Z"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

---

## USSD

### POST /ussd

Africa's Talking-style USSD handler.
Returns a string prefixed with `CON ` (continue, show input) or `END ` (session over).

**Content-Type:** `application/x-www-form-urlencoded` OR `application/json`

**Request (form or JSON)**
```json
{
  "sessionId": "ATsessionid123",
  "serviceCode": "*123#",
  "phoneNumber": "+27831234567",
  "text": "1*+27831234567*1234"
}
```

**Notes on `text`**
- Empty string `""`: first screen
- Each user input is appended with `*` separator
- Examples:
  - `""` → welcome screen
  - `"1"` → selected "New user"
  - `"1*ZA"` → selected South Africa as country
  - `"2*+27831234567*1234"` → login attempt

**Response 200** (plain text, not JSON)
```
CON Main Menu
1. Check a message
2. Scam examples
3. My account
4. Change language
5. Exit
```
or
```
END Thank you for using Mukuru Detection. Stay safe!
```

---

## SMS

### POST /sms/inbound

Receive an SMS from the simulator (or a real gateway in future).

**Request**
```json
{
  "from": "+27831234567",
  "body": "1",
  "timestamp": "2026-10-01T10:10:00Z"
}
```

**Response 200**
```json
{
  "status": "received",
  "reply": "Mukuru: HIGH RISK - Fake job offer. Do not pay upfront fees. Reply HELP for more."
}
```

---

### GET /sms/outbox

Return the authenticated user's SMS outbox messages.

**Headers:** `Authorization: Bearer <token>`

**Query params:** `limit` (default 20), `offset` (default 0)

**Response 200**
```json
{
  "messages": [
    {
      "id": "uuid",
      "direction": "outbound",
      "sender": "MukuruAlert",
      "body": "Scam of the Week: Watch out for fake job offers...",
      "created_at": "2026-10-01T08:00:00Z"
    }
  ],
  "total": 3,
  "limit": 20,
  "offset": 0
}
```

---

## Panic

### POST /panic

Activate emergency / decoy mode for the current session.
Writes a silent alert to the trusted contact's simulated SMS outbox.
Logs a `panic_triggered` audit event.

**Headers:** `Authorization: Bearer <token>`

**Request body:** empty `{}`

**Response 200**
```json
{
  "status": "ok"
}
```

**Notes**
- All subsequent requests in this session use decoy data
- No field in the response indicates duress mode is active

**Errors**
- `401` — missing or invalid token

---

## Login Guard

### POST /login-guard/event

Log a dating-app login guard event. Returns a check-in question.
If the user answers `"yes"`, raises their risk state for 60 minutes
(affects `AFTER_RISKY_MESSAGE` in transaction checks).

**Headers:** `Authorization: Bearer <token>`

**Request**
```json
{
  "event_type": "dating_app_login",
  "answer": null
}
```

Or with the check-in answer:
```json
{
  "event_type": "dating_app_login",
  "answer": "yes"
}
```

**Response 200 (no answer yet)**
```json
{
  "checkin_question": "Has someone you met online asked you for money?",
  "status": "awaiting_answer"
}
```

**Response 200 (answer = "yes")**
```json
{
  "status": "risk_raised",
  "advice": ["TRUST_YOUR_INSTINCTS", "DO_NOT_PAY_UPFRONT", "BLOCK_AND_REPORT"],
  "explanation": "This is a common romance scam pattern. People met online who quickly ask for money are almost always scammers."
}
```

**Response 200 (answer = "no")**
```json
{
  "status": "ok",
  "advice": []
}
```

---

## Scam Library

### GET /scams/library

Return the scam education library.

**Query params:**
- `lang` (default `en`): language code for translated strings
- `category` (optional): filter by category

**Response 200**
```json
{
  "lang": "en",
  "entries": [
    {
      "id": "fake_job_001",
      "category": "fake_job_offer",
      "example_message": "Congratulations! You've been selected for a work-from-home job...",
      "red_flags": ["FAKE_JOB_OFFER", "ASKS_FOR_MONEY", "MOVE_TO_WHATSAPP"],
      "red_flags_translated": [
        "Offers a job with suspicious conditions",
        "Asks you to send money or pay a fee",
        "Asks you to move the conversation to WhatsApp"
      ],
      "advice": ["DO_NOT_PAY_UPFRONT", "VERIFY_SENDER"]
    }
  ]
}
```

---

## Error Response Format

All error responses use this shape:

```json
{
  "error": "error_code_snake_case",
  "message": "Human-readable description",
  "field": "field_name_if_validation_error"
}
```

---

## Common HTTP Status Codes

| Code | Meaning                                      |
|------|----------------------------------------------|
| 200  | Success                                      |
| 201  | Resource created                             |
| 400  | Bad request / validation error               |
| 401  | Unauthenticated (missing or invalid token)   |
| 404  | Resource not found                           |
| 409  | Conflict (e.g. duplicate phone)              |
| 422  | Unprocessable entity (business rule blocked) |
| 429  | Rate limit exceeded                          |
| 500  | Internal server error                        |

---

## Environment Variables Reference

| Variable                | Default       | Description                                              |
|-------------------------|---------------|----------------------------------------------------------|
| `DATABASE_URL`          | `sqlite:///./mukuru.db` | SQLAlchemy connection string                |
| `SECRET_KEY`            | required      | Token signing key (any random string for dev)            |
| `MOCK_SAFE_BROWSING`    | `true`        | Use local blocklist instead of Google Safe Browsing API  |
| `SAFE_BROWSING_API_KEY` | —             | Google Safe Browsing API key (needed when mock=false)    |
| `LLM_ENABLED`           | `false`       | Enable LLM fallback classifier                           |
| `LLM_API_KEY`           | —             | OpenAI-compatible API key                                |
| `LLM_BASE_URL`          | —             | OpenAI-compatible base URL                               |
| `LLM_MODEL`             | `gpt-4o-mini` | Model name                                               |
| `RULES_WEIGHT`          | `0.6`         | Weight for rules score in final blend                    |
| `CLASSIFIER_WEIGHT`     | `0.4`         | Weight for classifier score in final blend               |
| `CORS_ORIGINS`          | `http://localhost:5173` | Comma-separated allowed CORS origins            |
