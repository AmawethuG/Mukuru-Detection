# Implementation Plan — Mukuru Detection Frontend

> Workspace root: `/Users/zamadangwana/Mukuru-Detection`
> All paths below are absolute. The `web/` directory is currently empty — the scaffold step creates it.
> Do NOT modify anything under `shared/`, `i18n/`, or `docs/`.

---

## Reference files (read before touching any code)

- API shapes: `/Users/zamadangwana/Mukuru-Detection/docs/api_contract.md`
- i18n keys: `/Users/zamadangwana/Mukuru-Detection/i18n/en.json`
- Code vocabulary: `/Users/zamadangwana/Mukuru-Detection/shared/reason_codes.json`
- Screen/routing design: `/Users/zamadangwana/Mukuru-Detection/.kiro/specs/mukuru-detection/design.md`

---

- [ ] 1. Scaffold the Vite + React-TS project and install all dependencies.

      Run the following commands **in this exact order**:

      ```sh
      cd /Users/zamadangwana/Mukuru-Detection
      npm create vite@latest web -- --template react-ts
      cd /Users/zamadangwana/Mukuru-Detection/web
      npm install
      npm install -D tailwindcss@3 postcss autoprefixer
      npx tailwindcss init -p
      npm install react-router-dom@6 zustand
      ```

      After running the commands, make these edits:

      **`/Users/zamadangwana/Mukuru-Detection/web/tailwind.config.js`** — set the content array:
      ```js
      content: ["./index.html", "./src/**/*.{ts,tsx}"],
      ```

      **`/Users/zamadangwana/Mukuru-Detection/web/src/index.css`** — replace entire file with:
      ```css
      @tailwind base;
      @tailwind components;
      @tailwind utilities;
      ```

      **`/Users/zamadangwana/Mukuru-Detection/web/vite.config.ts`** — ensure no changes needed beyond what Vite generates; leave as-is unless the build step later requires adjustment.

      Copy i18n files into public:
      ```sh
      mkdir -p /Users/zamadangwana/Mukuru-Detection/web/public/i18n
      cp /Users/zamadangwana/Mukuru-Detection/i18n/*.json /Users/zamadangwana/Mukuru-Detection/web/public/i18n/
      ```

      Files created/modified:
      - `/Users/zamadangwana/Mukuru-Detection/web/` (entire scaffold)
      - `/Users/zamadangwana/Mukuru-Detection/web/tailwind.config.js`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/index.css`
      - `/Users/zamadangwana/Mukuru-Detection/web/public/i18n/en.json` (copied)

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npm run build` — must exit 0 (the default Vite template builds cleanly before any of our code is added).

---

- [ ] 2. Create API client files in `web/src/api/`.

      Create the base fetch wrapper first, then each endpoint module. All files use TypeScript strict mode. API base URL is always `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`. Bearer token is read from `localStorage.getItem("token")`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/client.ts`**
      ```typescript
      const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

      export async function apiFetch<T>(
        path: string,
        options: RequestInit = {}
      ): Promise<T> {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          ...(options.headers as Record<string, string>),
        };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(`${BASE}${path}`, { ...options, headers });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw Object.assign(new Error(body.message ?? res.statusText), { status: res.status, body });
        }
        return res.json() as Promise<T>;
      }

      // For endpoints that return plain text (USSD)
      export async function apiFetchText(
        path: string,
        options: RequestInit = {}
      ): Promise<string> {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          ...(options.headers as Record<string, string>),
        };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const res = await fetch(`${BASE}${path}`, { ...options, headers });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.text();
      }
      ```

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/scan.ts`**
      — POST /scan. Request body: `{ text: string; channel: "web"|"sms"|"email"|"ussd"; user_id?: string }`.
        Response: `{ id, score, tier, category, reasons, advice, explanation, explanation_source, detected_language, scanned_at }`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/ussd.ts`**
      — POST /ussd. Sends JSON body with `{ sessionId, serviceCode, phoneNumber, text }`.
        Returns plain text (use `apiFetchText`). Name the exported function `postUssd`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/auth.ts`**
      — `postLogin({ phone, pin })` → POST /login → `{ token, user }`.
        `postRegister({ phone, country, language, pin, duress_pin, trusted_contact? })` → POST /register → `{ token, user }`.
        `getMe()` → GET /accounts/me → full account object.
        `patchMe({ language })` → PATCH /accounts/me → `{ language }`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/transactions.ts`**
      — `postTransactionCheck({ recipient, amount, currency, country })` → POST /transactions/check.
        `postTransactionSend({ recipient, amount, currency, country, force })` → POST /transactions/send.
        `getTransactionHistory({ limit?, offset? })` → GET /transactions/history.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/sms.ts`**
      — `getSmsOutbox({ limit?, offset? })` → GET /sms/outbox.
        `postSmsInbound({ from: string; body: string; timestamp: string })` → POST /sms/inbound → `{ status, reply }`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/panic.ts`**
      — `postPanic()` → POST /panic with empty body `{}` → `{ status }`.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/loginGuard.ts`**
      — `postLoginGuardEvent({ event_type: string; answer: "yes"|"no"|null })` → POST /login-guard/event.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/api/library.ts`**
      — `getScamsLibrary({ lang?, category? })` → GET /scams/library.

      All request/response types must be typed interfaces in the same file. Export named functions only (no default exports).

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/client.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/scan.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/ussd.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/auth.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/transactions.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/sms.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/panic.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/loginGuard.ts`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/api/library.ts`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero TypeScript errors in api/ files.

---

- [ ] 3. Create the Zustand global store at `web/src/store/useStore.ts`.

      Implement the following interface exactly:
      ```typescript
      interface User {
        id: string;
        phone: string;
        country: string;
        language: string;
        created_at: string;
      }

      interface AppState {
        token: string | null;
        user: User | null;
        language: string;           // defaults to "en"
        isDuress: boolean;          // defaults to false
        setToken: (t: string) => void;
        setUser: (u: User) => void;
        setLanguage: (l: string) => void;
        setDuress: (d: boolean) => void;
        logout: () => void;         // clears token, user, isDuress; keeps language
      }
      ```

      Persistence strategy (no Zustand middleware — use plain `subscribe`):
      - On store creation, read `localStorage.getItem("token")` and `localStorage.getItem("language")` to seed initial state.
      - After creating the store, call `useStore.subscribe(state => { ... })` to write `state.token` and `state.language` back to localStorage whenever they change. If `token` is null, call `localStorage.removeItem("token")`.
      - `logout()` must also call `localStorage.removeItem("token")`.

      Note: do NOT use `zustand/middleware` `persist` — it creates type complexity. The manual subscribe approach is simpler and sufficient.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/store/useStore.ts`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 4. Create the i18n helper at `web/src/i18n/index.ts`.

      ```typescript
      // Runtime i18n loader — reads JSON files from web/public/i18n/ via fetch
      // Languages available: en, zu, fr, sw, st, hi, nl, pt

      const cache: Record<string, Record<string, string>> = {};

      /** Lazy-load a language file. Safe to call multiple times. */
      export async function loadLanguage(lang: string): Promise<void> {
        if (cache[lang]) return;
        try {
          const res = await fetch(`/i18n/${lang}.json`);
          if (!res.ok) throw new Error(`Failed to load ${lang}`);
          const data = await res.json();
          cache[lang] = data;
        } catch {
          // Silently fall back; t() will use 'en'
        }
      }

      /** Translate a key. Falls back to 'en', then returns the key itself. */
      export function t(key: string, lang: string): string {
        return cache[lang]?.[key] ?? cache["en"]?.[key] ?? key;
      }

      // Pre-load English on module import (synchronous after first await resolves)
      loadLanguage("en");
      ```

      Also export a constant:
      ```typescript
      export const SUPPORTED_LANGUAGES = [
        { code: "en", label: "English" },
        { code: "zu", label: "isiZulu" },
        { code: "fr", label: "Français" },
        { code: "sw", label: "Kiswahili" },
        { code: "st", label: "Sesotho" },
        { code: "hi", label: "हिन्दी" },
        { code: "nl", label: "Nederlands" },
        { code: "pt", label: "Português" },
      ] as const;
      ```

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/i18n/index.ts`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 5. Create the `PhoneFrame` component at `web/src/components/PhoneFrame.tsx`.

      Props: `{ children: ReactNode; title?: string }`.

      Layout (Tailwind, no external library):
      - Outer wrapper: `mx-auto w-[280px]` with vertical centering helpers.
      - Phone shell: `bg-gray-800 rounded-[2.5rem] px-4 pt-6 pb-8 shadow-2xl flex flex-col gap-0`; fixed size via `h-[520px]`.
      - Top notch bar: `flex justify-center items-center h-6 mb-2` with a small `w-16 h-1.5 bg-black rounded-full` pill, and a tiny `w-2 h-2 bg-gray-600 rounded-full` circle to the right (camera dot).
      - Screen area: `flex-1 bg-black rounded-2xl overflow-hidden flex flex-col` with inner glow `shadow-inner`.
        - Title bar (if `title` prop is set): `bg-gray-900 text-green-400 font-mono text-xs px-3 py-1 text-center tracking-widest border-b border-green-900`.
        - Content area: `flex-1 overflow-y-auto font-mono text-green-400 text-sm p-3 leading-relaxed`.
      - Bottom bar: `h-8 flex justify-center items-center mt-2` with a `w-10 h-10 bg-gray-700 rounded-full border-2 border-gray-600` home button circle.

      All text inside the screen area must appear green-on-black monospace. The `children` renders inside the content area div.

      Add a comment at the top: `// PhoneFrame — Nokia-style phone shell for USSD and SMS simulators`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/components/PhoneFrame.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 6. Create the `ResultCard` component at `web/src/components/ResultCard.tsx`.

      Props interface:
      ```typescript
      interface ResultCardProps {
        tier: "SAFE" | "CAUTION" | "HIGH_RISK";
        score: number;
        category: string;
        reasons: string[];   // reason code strings, e.g. "FAKE_JOB_OFFER"
        advice: string[];    // advice code strings, e.g. "DO_NOT_PAY_UPFRONT"
        lang: string;
      }
      ```

      Tier styling map (define as a const inside the file):
      ```typescript
      const TIER_STYLES = {
        SAFE:      { bg: "bg-green-100",  text: "text-green-800",  icon: "✓", label: "Safe" },
        CAUTION:   { bg: "bg-yellow-100", text: "text-yellow-800", icon: "⚠", label: "Caution" },
        HIGH_RISK: { bg: "bg-red-100",    text: "text-red-800",    icon: "✗", label: "High Risk" },
      } as const;
      ```

      Reason code → i18n key map (define as a const in the file):
      ```typescript
      const REASON_KEYS: Record<string, string> = {
        FAKE_JOB_OFFER:      "reason.fake_job_offer",
        ASKS_FOR_MONEY:      "reason.asks_for_money",
        MOVE_TO_WHATSAPP:    "reason.move_to_whatsapp",
        SUSPICIOUS_LINK:     "reason.suspicious_link",
        REQUESTS_OTP_PIN:    "reason.requests_otp_pin",
        URGENCY_LANGUAGE:    "reason.urgency_language",
        IMPERSONATION:       "reason.impersonation",
        ADVANCE_FEE:         "reason.advance_fee",
        ROMANCE_SCAM:        "reason.romance_scam",
        LOOKALIKE_DOMAIN:    "reason.lookalike_domain",
        SHORTENED_URL:       "reason.shortened_url",
        PHONE_IN_MESSAGE:    "reason.phone_in_message",
        GENERIC_GREETING:    "reason.generic_greeting",
        EMAIL_MISMATCH:      "reason.email_mismatch",
        DISPLAY_NAME_SPOOF:  "reason.display_name_spoof",
        NEW_RECIPIENT:       "txn_reason.new_recipient",
        UNUSUAL_AMOUNT:      "txn_reason.unusual_amount",
        ROUND_LARGE_AMOUNT:  "txn_reason.round_large_amount",
        RAPID_REPEAT_SENDS:  "txn_reason.rapid_repeat_sends",
        AFTER_RISKY_MESSAGE: "txn_reason.after_risky_message",
        NEW_COUNTRY:         "txn_reason.new_country",
      };
      ```

      Advice code → i18n key map:
      ```typescript
      const ADVICE_KEYS: Record<string, string> = {
        DO_NOT_SHARE_PIN:   "advice.do_not_share_pin",
        DO_NOT_PAY_UPFRONT: "advice.do_not_pay_upfront",
        VERIFY_SENDER:      "advice.verify_sender",
        DO_NOT_CLICK_LINK:  "advice.do_not_click_link",
        PAUSE_AND_CONFIRM:  "advice.pause_and_confirm",
        REPORT_SCAM:        "advice.report_scam",
        TRUST_YOUR_INSTINCTS:"advice.trust_your_instincts",
        BLOCK_AND_REPORT:   "advice.block_and_report",
        CHECK_URL:          "advice.check_url",
      };
      ```

      Rendering rules:
      - Top banner: `${TIER_STYLES[tier].bg} ${TIER_STYLES[tier].text}` — shows `{icon} {label}` prominently (font-bold text-lg) plus the score as a pill badge: `<span class="ml-2 px-2 py-0.5 rounded-full text-sm font-mono">{score} / 100</span>`.
      - Category: `t("category." + category, lang)` — show in a subtle subtitle line.
      - Reasons section (max 3): heading from `t("scan.result.reasons_title", lang)`. Each reason: `t(REASON_KEYS[code] ?? code, lang)`. Render as a `<ul>` with bullet items.
      - Advice section: heading from `t("scan.result.advice_title", lang)`. Each item: `t(ADVICE_KEYS[code] ?? code, lang)`. Render as a numbered `<ol>`.
      - Never omit icon or text label — the tier must always be communicated via both colour AND icon AND text (accessibility requirement).
      - Wrap entire card in `<article role="region" aria-label={...}>` for screen reader accessibility.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/components/ResultCard.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 7. Create the `LanguageSwitcher` component at `web/src/components/LanguageSwitcher.tsx`.

      A `<select>` element that:
      - Renders all 8 language options using the `SUPPORTED_LANGUAGES` constant from `web/src/i18n/index.ts`.
      - Reads current language from `useStore(s => s.language)`.
      - On change: calls `setLanguage(newLang)` from the store AND calls `loadLanguage(newLang)` from i18n.
      - Styled as: `border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:ring-2 focus:ring-blue-500`.
      - Has a `<label>` element (visually hidden with `sr-only`) for accessibility: "Select language".

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/components/LanguageSwitcher.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 8. ⭐ Create the USSD Simulator page at `web/src/pages/USSDSimulator.tsx`.

      This is the centrepiece demo screen. Implement it fully and exactly as specified.

      **Imports needed:**
      - `useState` from react
      - `postUssd` from `../api/ussd`
      - `PhoneFrame` from `../components/PhoneFrame`

      **State (use exactly these names and initial values):**
      ```typescript
      const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
      const [text, setText] = useState("");
      const [displayText, setDisplayText] = useState("Press Send to connect…");
      const [inputValue, setInputValue] = useState("");
      const [isEnded, setIsEnded] = useState(false);
      const [isLoading, setIsLoading] = useState(false);
      const [error, setError] = useState<string | null>(null);
      const [ussdPhone, setUssdPhone] = useState("+27831234567");
      ```

      **`handleSend` function (exact implementation):**
      ```typescript
      async function handleSend() {
        if (isEnded || isLoading) return;
        const newText = text === "" ? inputValue : `${text}*${inputValue}`;
        setIsLoading(true);
        setError(null);
        try {
          const response = await postUssd({
            sessionId,
            serviceCode: "*123#",
            phoneNumber: ussdPhone,
            text: newText,
          });
          setText(newText);
          setInputValue("");
          if (response.startsWith("CON ")) {
            setDisplayText(response.slice(4));
          } else if (response.startsWith("END ")) {
            setDisplayText(response.slice(4));
            setIsEnded(true);
          } else {
            setDisplayText(response);
          }
        } catch {
          setError("Cannot connect to server. Check the backend is running on port 8000.");
        } finally {
          setIsLoading(false);
        }
      }
      ```

      **`handleClear` function (exact implementation):**
      ```typescript
      function handleClear() {
        setSessionId(crypto.randomUUID());
        setText("");
        setDisplayText("Press Send to connect…");
        setInputValue("");
        setIsEnded(false);
        setError(null);
      }
      ```

      **Keypad:** 4×3 grid of buttons for: `1 2 3 / 4 5 6 / 7 8 9 / * 0 #`. Each button calls `setInputValue(v => v + key)`. Style each button as `w-12 h-12 bg-gray-700 text-white font-mono text-lg rounded-full flex items-center justify-center hover:bg-gray-600 active:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-green-400`. The 4×3 grid uses `grid grid-cols-3 gap-3`.

      **Inside PhoneFrame (screen area content):**
      1. Error line (if `error !== null`): `<div className="text-red-400 text-xs mb-2">⚠ {error}</div>`
      2. Display text: `<pre className="whitespace-pre-wrap text-green-400 font-mono text-sm mb-2">{isLoading ? displayText + "\n…" : displayText}</pre>`
      3. Input line (when `!isEnded`): `<div className="flex items-center gap-1 border-t border-green-900 pt-2 mt-auto"><span className="text-green-600">&gt;</span><span className="text-green-400 font-mono text-sm">{inputValue}<span className="animate-pulse">|</span></span></div>`

      **Below PhoneFrame (when `!isEnded`):**
      - Phone number pill input: `<input type="tel" value={ussdPhone} onChange={e => setUssdPhone(e.target.value)} className="border border-gray-300 rounded-full px-4 py-1 text-sm text-center w-[200px] focus:ring-2 focus:ring-green-400" placeholder="+27831234567" aria-label="Simulated phone number" />`  — place this ABOVE the PhoneFrame div.
      - Keypad grid (below PhoneFrame)
      - SEND button: `<button onClick={handleSend} disabled={isLoading || isEnded} className="w-full py-2 bg-green-700 text-white font-bold rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed">SEND</button>`
      - CLEAR button: `<button onClick={handleClear} className="w-full py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 text-sm">CLEAR / NEW SESSION</button>`

      **When `isEnded`:** replace keypad and SEND with only: `<button onClick={handleClear} className="w-full py-2 bg-green-700 text-white font-bold rounded-lg hover:bg-green-600">NEW SESSION</button>`.

      **Demo shortcuts panel** (rendered below the phone frame + keypad, always visible):
      ```tsx
      <div className="mt-6 border-t pt-4">
        <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Demo shortcuts</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => { setUssdPhone("+27831234567"); handleClear(); }}
            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200"
          >
            Log in as Blessing
          </button>
          <button
            onClick={() => { setUssdPhone("+263771234567"); handleClear(); }}
            className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm hover:bg-purple-200"
          >
            Log in as Tendai
          </button>
          <button
            onClick={() => { handleClear(); setTimeout(() => setUssdPhone("+27831234567"), 0); }}
            className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm hover:bg-orange-200"
          >
            Check sample scam
          </button>
        </div>
      </div>
      ```

      **Page layout:** centre everything in a `<div className="max-w-sm mx-auto px-4 py-8">` wrapper with a heading `<h1 className="text-xl font-bold text-center mb-4">USSD Simulator</h1>`.

      **Accessibility:** all buttons must have descriptive aria-labels or visible text. The phone number input has `aria-label="Simulated phone number"`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/USSDSimulator.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 9. Create the Scan page at `web/src/pages/Scan.tsx`.

      State: `text`, `channel` ("web"|"sms"|"email"|"ussd"), `result` (scan response or null), `isLoading`, `error`.

      UI elements:
      - Page title from `t("scan.title", lang)`.
      - `<textarea>` with placeholder from `t("scan.placeholder", lang)`, bound to `text` state. Min-height `h-32`.
      - Channel `<select>` with options: web, sms, email, ussd (labels from `t("scan.channel.web", lang)` etc).
      - "Load demo scam" button: sets `text` to the value of `t("demo.sample_scams.fake_job", lang)`.
      - Submit button: calls `postScan({ text, channel })` from `../api/scan`. Shows `t("scan.scanning", lang)` while loading. Disabled if `text.trim() === ""` or `isLoading`.
      - On success: renders `<ResultCard tier={result.tier} score={result.score} category={result.category} reasons={result.reasons} advice={result.advice} lang={lang} />`.
      - Error: shows `t("common.error", lang)` in red text.
      - Loading spinner: a simple `animate-spin` border div (Tailwind: `w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto`).

      Read `lang` from `useStore(s => s.language)`.
      Read `user` from `useStore(s => s.user)` and pass `user?.id` as `user_id` to `postScan` if available.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Scan.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 10. Create the Login page at `web/src/pages/Login.tsx`.

      State: `phone`, `pin`, `isLoading`, `error`.

      Behaviour:
      - On submit: call `postLogin({ phone, pin })` from `../api/auth`. On success: call `setToken(res.token)` and `setUser(res.user)` from the store, then `navigate("/home")` via `useNavigate()`.
      - Error 401: show `t("auth.error.invalid_credentials", lang)`.
      - Error 429: show `t("auth.error.too_many_attempts", lang)`.

      Demo section: two buttons styled as outlined cards:
      - "Blessing (+27831234567 / 1234)": sets phone="+27831234567", pin="1234" and immediately submits.
      - "Tendai (+263771234567 / 1234)": sets phone="+263771234567", pin="1234" and immediately submits.
      - The demo buttons call a `handleDemoLogin(phone, pin)` helper that sets state and calls the login API directly (don't rely on form submit event).

      Link to `/register` using `<Link to="/register">`.

      Fields:
      - Phone: `<input type="tel" autoComplete="tel">` with label `t("auth.login.phone", lang)`.
      - PIN: `<input type="password" maxLength={4} inputMode="numeric">` with label `t("auth.login.pin", lang)`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Login.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 11. Create the Register page at `web/src/pages/Register.tsx`.

      State: `phone`, `country`, `language`, `pin`, `pinConfirm`, `duressPin`, `duressPinConfirm`, `isLoading`, `error`.

      Client-side validation before API call:
      - PIN must be exactly 4 digits.
      - PIN and confirm must match.
      - Duress PIN must differ from PIN.
      - Phone must match `/^\+\d{7,15}$/`.

      On success: call `setToken` + `setUser`, then `navigate("/home")`.

      Country `<select>` options: ZA, ZW, MZ, AO, CD, TZ, KE, IN, NL, BE, FR, OTHER (labels from `t("country.ZA", lang)` etc).
      Language `<select>` options: en, zu, fr, sw, st, hi, nl, pt (labels from `t("language.en", lang)` etc).

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Register.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 12. Create the Home page at `web/src/pages/Home.tsx`.

      State: `showPanicModal` (boolean), `isPanicking` (boolean).

      UI:
      - Welcome: `t("app.name", lang)` heading + "Welcome, {user.phone}" sub-heading.
      - 4 quick-action cards in a `grid grid-cols-2 gap-4`:
        - "Check a Message" → `/scan`
        - "Send Money" → `/send`
        - "USSD Simulator" → `/ussd`
        - "Learn the Scams" → `/learn`
        Each card: `block p-4 bg-white rounded-xl shadow hover:shadow-md text-center font-semibold`. Use `<Link>` from react-router-dom.
      - Panic button: fixed `bottom-4 right-4` floating button labelled `t("panic.button_label", lang)` in `bg-red-600 text-white rounded-full px-4 py-2 shadow-lg hover:bg-red-700`. On click: set `showPanicModal=true`.
      - Panic modal (when `showPanicModal`): overlay with confirm/cancel. On confirm: call `postPanic()`, then `setDuress(true)`, close modal, `navigate("/history")`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Home.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 13. Create the Send page at `web/src/pages/Send.tsx`.

      State: `recipient`, `amount`, `currency` (default "ZAR"), `country` (default "ZW"), `checkResult` (risk check response or null), `isSending`, `isChecking`, `error`, `successMsg`.

      Flow:
      1. User fills form and clicks "Check & Send".
      2. POST /transactions/check → show `<ResultCard>` with check result.
      3. If tier is `HIGH_RISK`: show "Pause — I'll check first" and "Send anyway" buttons.
         - "Pause" → clear result, stay on page.
         - "Send anyway" → POST /transactions/send with `force: true`.
      4. If tier is `SAFE` or `CAUTION`: single "Confirm & Send" button → POST /transactions/send with `force: false`.
      5. On send success: show `t("send.success", lang)` in green.
      6. Handle 422 from send (re-blocked): show the risk card again with the error response data.

      Currency options: ZAR, USD, ZWL, MZN, EUR.
      Country options: same list as Register.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Send.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 14. Create the History page at `web/src/pages/History.tsx`.

      On mount: call `getMe()` to fetch account + `getTransactionHistory({})`.

      Display:
      - Balance: `t("history.balance", lang)`: `{account.balance} {account.currency}`.
      - Transaction list: each item shows direction icon (↑ sent / ↓ received), recipient, amount + currency, date (formatted as locale string), status badge.
      - Empty state: `t("history.no_transactions", lang)`.
      - If `isDuress` is true in the store: show a small notice "Decoy account – demo mode active" (subtle gray text, bottom of list). This is not the real duress flag — the backend already returns decoy data when the session is duress; this note just helps demo observers understand what they're seeing.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/History.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 15. Create the Learn page at `web/src/pages/Learn.tsx`.

      On mount: call `getScamsLibrary({ lang })`.

      UI:
      - Page title: `t("learn.title", lang)`.
      - Category filter `<select>` populated from unique categories in the response.
      - Entry cards: show category heading, example message (in a `<blockquote>`), red flags list (translated using `REASON_KEYS` from ResultCard — import the map or duplicate locally), advice list.
      - Empty state: `t("learn.no_entries", lang)`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Learn.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 16. Create the LoginGuard page at `web/src/pages/LoginGuard.tsx`.

      State: `phase` ("idle" | "awaiting_answer" | "done"), `question`, `status`, `advice`, `isLoading`.

      Flow:
      1. "Simulate dating-app login" button → POST /login-guard/event `{ event_type: "dating_app_login", answer: null }` → shows checkin question + yes/no buttons, `phase = "awaiting_answer"`.
      2. "Yes" → POST /login-guard/event `{ event_type: "dating_app_login", answer: "yes" }` → show risk advice, `phase = "done"`.
      3. "No" → POST with `answer: "no"` → show `t("login_guard.no_response", lang)`, `phase = "done"`.

      Show `t("login_guard.simulation_notice", lang)` always on screen.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/LoginGuard.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 17. Create the SMSSimulator page at `web/src/pages/SMSSimulator.tsx`.

      State: `messages` (array of outbox+reply pairs), `inputBody`, `isLoading`, `error`.

      On mount: call `getSmsOutbox({})` and set `messages` from the response.

      UI — all wrapped in `<PhoneFrame title="SMS Simulator">`:
      - Outbox messages rendered as chat-bubble divs (outbound on right, inbound on left), green-on-black monospace style.
      - Input area at bottom of screen: text input + "SEND" button. On send: call `postSmsInbound({ from: user.phone, body: inputBody, timestamp: new Date().toISOString() })`. Append the sent message + the `reply` field from the response as a new inbound message into the `messages` array. Clear `inputBody`.
      - Error: red text inside the screen area.

      Page layout: same `max-w-sm mx-auto px-4 py-8` wrapper as USSDSimulator.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/SMSSimulator.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 18. Create the Demo page at `web/src/pages/Demo.tsx`.

      UI:
      - Page title: `t("demo.title", lang)`.
      - Two user cards (Blessing and Tendai): show phone, PIN hint, one-click "Log in as Blessing" / "Log in as Tendai" buttons. These buttons call `postLogin` then `setToken` + `setUser` + `navigate("/home")`. Use `t("demo.login_as", lang).replace("{name}", "Blessing")` etc.
      - Sample scam cards: 5 cards (fake_job, phishing, romance, advance_fee, impersonation) each showing the message text from `t("demo.sample_scams.fake_job", lang)` etc. Each has a "Copy" button (uses `navigator.clipboard.writeText`) and a "Load in Scanner" button (navigates to `/scan` — since we can't pass state easily, use `useNavigate` with `state: { text: ... }` and handle it on the Scan page).

      For the "Load in Scanner" navigation: in `Scan.tsx`, add `const location = useLocation(); useEffect(() => { if (location.state?.text) setText(location.state.text); }, []);`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Demo.tsx`
      - `/Users/zamadangwana/Mukuru-Detection/web/src/pages/Scan.tsx` (minor addition: handle location.state.text)

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 19. Create `App.tsx` with full routing.

      **`/Users/zamadangwana/Mukuru-Detection/web/src/App.tsx`** (replace the Vite default entirely).

      Structure:
      ```tsx
      import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
      // import all pages
      // import Nav

      function ProtectedRoute({ children }: { children: ReactNode }) {
        const token = useStore(s => s.token);
        return token ? <>{children}</> : <Navigate to="/login" replace />;
      }

      export default function App() {
        return (
          <BrowserRouter>
            <Nav />
            <main className="md:pl-56 pb-16 md:pb-0 min-h-screen bg-gray-50">
              <Routes>
                <Route path="/" element={<RootRedirect />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
                <Route path="/scan" element={<ProtectedRoute><Scan /></ProtectedRoute>} />
                <Route path="/send" element={<ProtectedRoute><Send /></ProtectedRoute>} />
                <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
                <Route path="/learn" element={<Learn />} />
                <Route path="/ussd" element={<USSDSimulator />} />
                <Route path="/sms" element={<ProtectedRoute><SMSSimulator /></ProtectedRoute>} />
                <Route path="/demo" element={<Demo />} />
                <Route path="/login-guard" element={<ProtectedRoute><LoginGuard /></ProtectedRoute>} />
              </Routes>
            </main>
          </BrowserRouter>
        );
      }
      ```

      `RootRedirect`: reads `token` from store; if truthy → `<Navigate to="/home" replace />`, else → `<Navigate to="/login" replace />`.

      Also call `loadLanguage(initialLanguage)` once in `App.tsx` via `useEffect(() => { loadLanguage(language); }, [language])` (using `useStore`).

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/App.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 20. Create the Nav component at `web/src/components/Nav.tsx`.

      Design:
      - Mobile (default): sticky bottom bar `fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 flex justify-around items-center h-14 md:hidden`. Shows icons + short labels for: Home, Scan, Send, USSD, Learn.
      - Desktop (md+): fixed left sidebar `hidden md:flex fixed left-0 top-0 h-full w-56 flex-col bg-gray-900 text-white p-4 gap-2`. Shows all nav links: Home, Scan, Send, USSD, SMS, Learn, Demo, Login Guard. Below links: show user phone in small gray text. At bottom: `<LanguageSwitcher />` + Logout button.
      - Desktop header bar: `hidden md:flex fixed top-0 right-0 left-56 z-40 bg-white border-b border-gray-200 px-6 py-3 items-center justify-between h-14`. Shows app name left, `<LanguageSwitcher />` right.

      Active link: use `NavLink` from react-router-dom with `className={({ isActive }) => isActive ? "... bg-gray-700" : "..."}`.

      Nav link labels come from i18n: `t("nav.home", lang)`, `t("nav.scan", lang)`, etc.

      Logout button calls `logout()` from the store and navigates to `/login`.

      Files:
      - `/Users/zamadangwana/Mukuru-Detection/web/src/components/Nav.tsx`

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npx tsc --noEmit` — zero errors.

---

- [ ] 21. Final build verification and TypeScript error fixes.

      Run:
      ```sh
      cd /Users/zamadangwana/Mukuru-Detection/web && npm run build
      ```

      Expected outcome: Vite build completes with zero errors. The `dist/` folder is created.

      If there are TypeScript errors, fix them before considering this step done. Common issues to check:
      - Unused imports (TypeScript strict mode may flag them — remove or use `_`-prefix).
      - Missing return types on async functions — add `: Promise<void>` where needed.
      - `location.state` typing — cast as `{ text?: string } | null` before accessing `.text`.
      - Any `any` types — replace with proper interfaces.
      - Ensure `src/main.tsx` imports `./index.css` (Vite default does this; confirm it's preserved).

      After a clean build, also run the dev server briefly to do a smoke check:
      ```sh
      cd /Users/zamadangwana/Mukuru-Detection/web && npm run dev &
      sleep 3
      curl -s http://localhost:5173 | grep -q "Mukuru" && echo "Dev server OK" || echo "Dev server not returning expected content"
      kill %1
      ```

      Files potentially modified: any file with TypeScript errors discovered during build.

      Verify: `cd /Users/zamadangwana/Mukuru-Detection/web && npm run build` — exits 0, `dist/` folder present.

---

## Notes for the coder

1. **Step ordering matters.** Each step depends on the previous. Do not skip ahead — `ResultCard` (step 6) requires the i18n helper (step 4), and `App.tsx` (step 19) requires all pages to exist.

2. **The `web/` directory is currently empty.** Step 1 creates all scaffolding. Confirm the scaffold completed before writing any source files.

3. **i18n keys are authoritative.** Do not hardcode English strings in components. Always use `t(key, lang)` with keys from `/Users/zamadangwana/Mukuru-Detection/i18n/en.json`.

4. **USSD plain-text response.** The `/ussd` endpoint returns `Content-Type: text/plain`, not JSON. Use `apiFetchText` in `ussd.ts`, not `apiFetch`.

5. **USSD simulator is the star of the demo.** Get step 8 right — the error message when the backend is down, the `CON`/`END` prefix stripping, and the keypad must all work exactly as specified.

6. **No component libraries.** Tailwind only. No shadcn, no MUI, no Radix, no headlessui.

7. **TypeScript strict mode.** The Vite react-ts template enables `strict: true` in `tsconfig.json`. Do not relax it.

8. **Accessibility.** Every tier result (SAFE/CAUTION/HIGH_RISK) must show icon + text label + colour. Never colour alone.

9. **Mobile-first.** Base styles target 375px. Use `md:` prefixes for desktop-only layout changes.

10. **API base URL.** Always `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`. Never hardcode "localhost:8000" directly outside of `client.ts`.
