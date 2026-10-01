import { useState, useCallback, useRef, useEffect } from "react";
import { postUssd } from "../api/ussd";

// ── Types ─────────────────────────────────────────────────────────────────
interface UssdState {
  sessionId: string;
  phoneNumber: string;
  text: string;          // accumulated inputs joined by *
  display: string;       // current screen text (without CON/END prefix)
  inputValue: string;    // text being typed on the current screen
  isEnded: boolean;
  isLoading: boolean;
  error: string;
}

// ── Demo shortcuts ──────────────────────────────────────────────────────
const DEMO_SHORTCUTS = [
  {
    label: "Log in as Blessing",
    icon: "🇿🇦",
    phone: "+27831234567",
    // selects "Log in" → enters phone → enters PIN → arrives at main menu
    steps: ["2", "+27831234567", "1234"],
  },
  {
    label: "Log in as Tendai",
    icon: "🇿🇼",
    phone: "+263771234567",
    steps: ["2", "+263771234567", "1234"],
  },
];

const SAMPLE_SCAM =
  "Congratulations! You have been selected for a work-from-home job paying R5000/week. " +
  "To activate your position, pay a R500 registration fee via EFT. " +
  "WhatsApp +27600000001 to confirm.";

// ── Helpers ───────────────────────────────────────────────────────────────
function newSessionId() {
  return "AT" + Math.random().toString(36).slice(2, 12).toUpperCase();
}

function freshState(phone = "+27831234567"): UssdState {
  return {
    sessionId: newSessionId(),
    phoneNumber: phone,
    text: "",
    display: "",
    inputValue: "",
    isEnded: false,
    isLoading: false,
    error: "",
  };
}

// ── Keypad layout ─────────────────────────────────────────────────────────
const KEYPAD: string[][] = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["*", "0", "#"],
];

// ── Component ─────────────────────────────────────────────────────────────
export default function USSDSimulator() {
  const [state, setState] = useState<UssdState>(() => freshState());
  const displayRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll the screen when new content arrives
  useEffect(() => {
    if (displayRef.current) {
      displayRef.current.scrollTop = displayRef.current.scrollHeight;
    }
  }, [state.display]);

  // Send the current inputValue to the backend
  const send = useCallback(async (overrideInput?: string) => {
    const value = overrideInput ?? state.inputValue;
    const newText = state.text
      ? state.text + "*" + value
      : value;

    setState((s) => ({ ...s, isLoading: true, error: "" }));

    try {
      const raw = await postUssd({
        sessionId: state.sessionId,
        serviceCode: "*123#",
        phoneNumber: state.phoneNumber,
        text: newText,
      });

      const isCon = raw.startsWith("CON ");
      const isEnd = raw.startsWith("END ");
      const displayText = isCon
        ? raw.slice(4)
        : isEnd
        ? raw.slice(4)
        : raw;

      setState((s) => ({
        ...s,
        text: newText,
        display: displayText,
        inputValue: "",
        isEnded: isEnd,
        isLoading: false,
      }));
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Cannot connect to server.";
      setState((s) => ({
        ...s,
        isLoading: false,
        error: `⚠ ${msg}\nMake sure the backend is running: uvicorn backend.main:app --reload`,
      }));
    }
  }, [state]);

  // Initialise — send empty text to get the welcome screen
  const init = useCallback(async (phone: string) => {
    const sid = newSessionId();
    setState({ ...freshState(phone), sessionId: sid, isLoading: true });
    try {
      const raw = await postUssd({
        sessionId: sid,
        serviceCode: "*123#",
        phoneNumber: phone,
        text: "",
      });
      const isEnd = raw.startsWith("END ");
      const displayText = raw.startsWith("CON ") || isEnd
        ? raw.slice(4)
        : raw;
      setState((s) => ({
        ...s,
        display: displayText,
        isEnded: isEnd,
        isLoading: false,
      }));
    } catch {
      setState((s) => ({
        ...s,
        isLoading: false,
        display: "",
        error: "⚠ Cannot connect to server.\nMake sure the backend is running: uvicorn backend.main:app --reload",
      }));
    }
  }, []);

  // Load welcome screen on mount
  useEffect(() => { init(state.phoneNumber); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Key press on the keypad
  function pressKey(key: string) {
    if (state.isEnded || state.isLoading) return;
    setState((s) => ({ ...s, inputValue: s.inputValue + key }));
    inputRef.current?.focus();
  }

  // Backspace
  function backspace() {
    setState((s) => ({
      ...s,
      inputValue: s.inputValue.slice(0, -1),
    }));
  }

  // Clear — full new session
  function clear() { init(state.phoneNumber); }

  // Demo shortcut — replay a sequence of inputs step-by-step
  async function runShortcut(phone: string, steps: string[]) {
    const sid = newSessionId();
    let text = "";
    setState({ ...freshState(phone), sessionId: sid, isLoading: true });

    // Walk through each pre-set input automatically
    for (const step of steps) {
      const newText = text ? text + "*" + step : step;
      try {
        const raw = await postUssd({
          sessionId: sid,
          serviceCode: "*123#",
          phoneNumber: phone,
          text: newText,
        });
        const isEnd = raw.startsWith("END ");
        const displayText = raw.slice(4);
        text = newText;
        setState((s) => ({
          ...s,
          text,
          display: displayText,
          isEnded: isEnd,
          isLoading: false,
        }));
        if (isEnd) return;
      } catch {
        setState((s) => ({
          ...s,
          isLoading: false,
          error: "⚠ Cannot connect to server.",
        }));
        return;
      }
      // Small delay so it feels like sequential input
      await new Promise((r) => setTimeout(r, 300));
    }
  }

  // "Check sample scam" — log in as Blessing then navigate to check-message
  async function checkSampleScam() {
    const phone = "+27831234567";
    // steps: login, main menu option 1, then paste the scam text
    const steps = ["2", phone, "1234", "1", SAMPLE_SCAM];
    await runShortcut(phone, steps);
  }

  return (
    <div className="section py-10">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-mukuru-navy mb-1">
          USSD Simulator
        </h1>
        <p className="text-mukuru-gray">
          Dial <strong className="text-mukuru-green">*123#</strong> — works on
          any phone, no internet needed. Try it right here in your browser.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 items-start">

        {/* ── Phone ───────────────────────────────────────────────────── */}
        <div className="flex flex-col items-center mx-auto lg:mx-0">

          {/* Phone number input (above the phone) */}
          <div className="mb-3 w-[280px]">
            <label className="block text-xs font-semibold text-mukuru-gray mb-1 text-center">
              Simulated phone number
            </label>
            <input
              type="tel"
              className="field text-center text-sm py-2"
              value={state.phoneNumber}
              onChange={(e) =>
                setState((s) => ({ ...s, phoneNumber: e.target.value }))
              }
              placeholder="+27831234567"
            />
          </div>

          {/* ── Outer phone shell ──────────────────────────────────── */}
          <div
            className="bg-gray-800 rounded-[2.5rem] p-3 shadow-2xl"
            style={{ width: 280 }}
          >
            {/* Top notch */}
            <div className="flex justify-center mb-2">
              <div className="bg-black rounded-full h-1.5 w-16" />
            </div>

            {/* Screen */}
            <div
              className="bg-black rounded-2xl overflow-hidden"
              style={{ minHeight: 260, maxHeight: 320 }}
            >
              {/* Status bar */}
              <div className="bg-gray-900 px-3 py-1 flex items-center justify-between">
                <span className="text-green-500 text-[10px] font-mono">
                  *123#
                </span>
                <span className="text-green-500 text-[10px] font-mono">
                  {state.sessionId.slice(0, 8)}
                </span>
                <span className="text-green-500 text-[10px]">▐▐▐</span>
              </div>

              {/* Display area */}
              <div
                ref={displayRef}
                className="px-3 py-2 overflow-y-auto font-mono text-green-400 text-[13px] leading-relaxed"
                style={{ minHeight: 180, maxHeight: 220 }}
                aria-live="polite"
                aria-label="USSD screen"
              >
                {state.isLoading && !state.display && (
                  <span className="opacity-60">Connecting…</span>
                )}
                {state.error ? (
                  <span className="text-red-400 text-[11px] whitespace-pre-wrap">
                    {state.error}
                  </span>
                ) : (
                  <span className="whitespace-pre-wrap">{state.display}</span>
                )}
              </div>

              {/* Input line (hidden when session ended) */}
              {!state.isEnded && !state.error && (
                <div className="px-3 pb-2 flex items-center gap-1 border-t border-gray-800">
                  <span className="text-green-600 font-mono text-[13px]">&gt;</span>
                  <input
                    ref={inputRef}
                    type="text"
                    className="flex-1 bg-transparent text-green-400 font-mono text-[13px]
                               outline-none caret-green-400 placeholder-green-800"
                    placeholder="type or use keypad"
                    value={state.inputValue}
                    onChange={(e) =>
                      setState((s) => ({ ...s, inputValue: e.target.value }))
                    }
                    onKeyDown={(e) => e.key === "Enter" && send()}
                    disabled={state.isLoading}
                  />
                  {/* Blinking cursor */}
                  <span className="text-green-400 font-mono text-[13px] animate-blink">
                    ▌
                  </span>
                </div>
              )}
            </div>

            {/* ── Keypad ──────────────────────────────────────────── */}
            <div className="mt-3 space-y-1.5">
              {KEYPAD.map((row, ri) => (
                <div key={ri} className="flex gap-1.5 justify-center">
                  {row.map((key) => (
                    <button
                      key={key}
                      onClick={() => pressKey(key)}
                      disabled={state.isEnded || state.isLoading}
                      aria-label={`Key ${key}`}
                      className="flex-1 h-10 bg-gray-700 hover:bg-gray-600 active:bg-gray-500
                                 text-green-400 font-mono font-bold text-sm rounded-lg
                                 transition-colors disabled:opacity-40 select-none"
                    >
                      {key}
                    </button>
                  ))}
                </div>
              ))}

              {/* Action row */}
              <div className="flex gap-1.5 justify-center mt-2">
                <button
                  onClick={backspace}
                  disabled={state.isEnded || state.isLoading || !state.inputValue}
                  className="flex-1 h-10 bg-gray-700 hover:bg-gray-600 text-yellow-400
                             font-mono text-xs rounded-lg transition-colors disabled:opacity-40"
                  aria-label="Backspace"
                >
                  ⌫
                </button>
                {state.isEnded ? (
                  <button
                    onClick={clear}
                    className="flex-[2] h-10 bg-mukuru-green hover:bg-mukuru-green-dark
                               text-white font-bold text-xs rounded-lg transition-colors"
                  >
                    NEW SESSION
                  </button>
                ) : (
                  <button
                    onClick={() => send()}
                    disabled={state.isLoading}
                    className="flex-[2] h-10 bg-mukuru-green hover:bg-mukuru-green-dark
                               text-white font-bold text-xs rounded-lg transition-colors
                               disabled:opacity-50"
                  >
                    {state.isLoading ? "…" : "SEND ✓"}
                  </button>
                )}
                <button
                  onClick={clear}
                  className="flex-1 h-10 bg-red-800 hover:bg-red-700 text-red-200
                             font-mono text-xs rounded-lg transition-colors"
                  aria-label="Clear session"
                >
                  CLR
                </button>
              </div>
            </div>

            {/* Bottom bar */}
            <div className="flex justify-center mt-3">
              <div className="bg-gray-700 rounded-full h-1 w-16" />
            </div>
          </div>
        </div>

        {/* ── Right panel: shortcuts + instructions ───────────────────── */}
        <div className="flex-1 space-y-5 w-full lg:max-w-md">
          {/* Demo shortcuts */}
          <div className="card">
            <h2 className="font-bold text-mukuru-navy mb-3">Demo shortcuts</h2>
            <div className="space-y-2">
              {DEMO_SHORTCUTS.map((s) => (
                <button
                  key={s.phone}
                  onClick={() => runShortcut(s.phone, s.steps)}
                  className="w-full text-left p-3 rounded-xl border border-mukuru-gray-border
                             hover:border-mukuru-green hover:bg-mukuru-green-light
                             transition-all flex items-center gap-3"
                >
                  <span className="text-2xl">{s.icon}</span>
                  <div>
                    <div className="font-semibold text-sm text-mukuru-navy">{s.label}</div>
                    <div className="text-xs text-mukuru-gray">{s.phone} · PIN 1234</div>
                  </div>
                </button>
              ))}

              <button
                onClick={checkSampleScam}
                className="w-full text-left p-3 rounded-xl border border-red-200
                           hover:border-red-400 hover:bg-red-50
                           transition-all flex items-center gap-3"
              >
                <span className="text-2xl">🚨</span>
                <div>
                  <div className="font-semibold text-sm text-red-700">Check sample scam</div>
                  <div className="text-xs text-mukuru-gray">
                    Logs in as Blessing and checks the fake job offer
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* How it works */}
          <div className="card">
            <h2 className="font-bold text-mukuru-navy mb-3">How to use</h2>
            <ol className="space-y-2 text-sm text-mukuru-gray list-decimal list-inside">
              <li>Enter your phone number above the phone.</li>
              <li>Use the keypad or type in the input to navigate menus.</li>
              <li>Press <strong>SEND</strong> or hit Enter to submit each input.</li>
              <li>Select option <strong>2</strong> to log in, then option <strong>1</strong> to check a message.</li>
              <li>Press <strong>CLR</strong> or <strong>NEW SESSION</strong> to start over.</li>
            </ol>
            <div className="mt-4 p-3 rounded-lg bg-mukuru-green-light border border-mukuru-green/20">
              <p className="text-xs text-mukuru-navy font-medium">
                💡 This connects to the real backend. Run{" "}
                <code className="bg-white px-1 rounded font-mono text-xs">
                  uvicorn backend.main:app --reload
                </code>{" "}
                to start it.
              </p>
            </div>
          </div>

          {/* USSD flow diagram */}
          <div className="card">
            <h2 className="font-bold text-mukuru-navy mb-3">Menu structure</h2>
            <pre className="text-xs text-mukuru-gray font-mono leading-relaxed overflow-x-auto">
{`*123#
├─ 1. New user
│   ├─ Enter phone
│   ├─ Choose country
│   ├─ Choose language
│   ├─ Set PIN
│   └─ Set duress PIN
└─ 2. Log in
    ├─ Enter phone + PIN
    └─ Main menu
        ├─ 1. Check a message ← scam detection
        ├─ 2. Scam examples
        ├─ 3. My account
        ├─ 4. Change language
        └─ 5. Exit`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
