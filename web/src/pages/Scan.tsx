import { useState } from "react";
import { scanMessage, type Channel, type ScanResponse } from "../api/scan";
import { ResultCard } from "../components/ResultCard";
import { useStore } from "../store/useStore";

const CHANNELS: { value: Channel; label: string; icon: string }[] = [
  { value: "sms", label: "SMS / text", icon: "💬" },
  { value: "web", label: "Website / app", icon: "🌐" },
  { value: "email", label: "Email", icon: "📧" },
  { value: "ussd", label: "USSD menu", icon: "📱" },
];

// Quick-load sample scam messages for the demo
const SAMPLES = [
  {
    label: "Fake job offer",
    icon: "💼",
    text: "Congratulations! You have been selected for a work-from-home job paying R5000/week. To activate your position, pay a R500 registration fee via EFT to account 1234567. WhatsApp +27600000001 to confirm.",
    channel: "sms" as Channel,
  },
  {
    label: "Phishing (ABSA)",
    icon: "🏦",
    text: "ABSA BANK: Your account has been suspended due to suspicious activity. Verify now at www.absa-secure-login.co to avoid permanent closure. Ref: 8823",
    channel: "sms" as Channel,
  },
  {
    label: "Romance scam",
    icon: "❤️",
    text: "My darling, I am stuck at customs in Dubai. They are holding my luggage and need $300 to release it. I will pay you back double when I arrive. Please help me, I love you.",
    channel: "web" as Channel,
  },
  {
    label: "Advance fee",
    icon: "💰",
    text: "Dear Beneficiary, you have been selected to receive $1.5 million from the estate of Dr. James Okafor. To release your funds, you must first pay a processing fee of $200 USD.",
    channel: "email" as Channel,
  },
  {
    label: "Legit bank OTP",
    icon: "✅",
    text: "Your Capitec OTP is 483921. Valid for 5 minutes. Do not share this code with anyone. If you did not request this, call 0860 10 20 43.",
    channel: "sms" as Channel,
  },
];

export default function Scan() {
  const { user, language } = useStore();
  const [text, setText] = useState("");
  const [channel, setChannel] = useState<Channel>("sms");
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) { setError("Please paste a message to check."); return; }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const res = await scanMessage(text.trim(), channel, user?.id);
      setResult(res);
    } catch {
      setError("Scan failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function loadSample(s: typeof SAMPLES[0]) {
    setText(s.text);
    setChannel(s.channel);
    setResult(null);
    setError("");
  }

  return (
    <div className="section py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-mukuru-navy mb-1">
          Check a Message
        </h1>
        <p className="text-mukuru-gray">
          Paste any SMS, email or message below. We'll tell you if it looks
          like a scam.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* ── Input panel ─────────────────────────────────────────── */}
        <div className="flex-1">
          <form onSubmit={handleScan} className="card space-y-4">
            {/* Channel selector */}
            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-2">
                How did you receive it?
              </label>
              <div className="flex flex-wrap gap-2">
                {CHANNELS.map((c) => (
                  <button
                    key={c.value}
                    type="button"
                    onClick={() => setChannel(c.value)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border transition-colors
                      ${channel === c.value
                        ? "bg-mukuru-green text-white border-mukuru-green"
                        : "border-mukuru-gray-border text-mukuru-gray hover:border-mukuru-green hover:text-mukuru-green"
                      }`}
                  >
                    <span aria-hidden="true">{c.icon}</span>
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Text area */}
            <div>
              <label
                htmlFor="message-input"
                className="block text-sm font-medium text-mukuru-navy mb-1"
              >
                Message or email text
              </label>
              <textarea
                id="message-input"
                className="field resize-none"
                rows={6}
                placeholder="Paste the suspicious message here…"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <div className="text-right text-xs text-mukuru-gray mt-1">
                {text.length}/10 000
              </div>
            </div>

            {error && (
              <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3.5">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Checking…
                </span>
              ) : (
                "Check this message →"
              )}
            </button>
          </form>

          {/* Result card */}
          {result && (
            <div className="mt-6">
              <ResultCard
                tier={result.tier}
                score={result.score}
                category={result.category}
                reasons={result.reasons}
                advice={result.advice}
                explanation={result.explanation}
                lang={language}
              />
              <p className="text-xs text-mukuru-gray mt-2 text-right">
                Detected language: <strong>{result.detected_language}</strong> ·
                Source: <strong>{result.explanation_source}</strong>
              </p>
            </div>
          )}
        </div>

        {/* ── Sample messages panel ────────────────────────────────── */}
        <div className="w-full lg:w-72 shrink-0">
          <div className="card">
            <h2 className="font-bold text-mukuru-navy mb-1">Try a sample</h2>
            <p className="text-xs text-mukuru-gray mb-3">
              Click any message to load it into the scanner.
            </p>
            <div className="space-y-2">
              {SAMPLES.map((s) => (
                <button
                  key={s.label}
                  onClick={() => loadSample(s)}
                  className={`w-full text-left p-3 rounded-xl border transition-all
                    ${text === s.text
                      ? "border-mukuru-green bg-mukuru-green-light"
                      : "border-mukuru-gray-border hover:border-mukuru-green hover:bg-mukuru-green-light/50"
                    }`}
                >
                  <div className="flex items-center gap-2 mb-0.5">
                    <span aria-hidden="true">{s.icon}</span>
                    <span className="text-sm font-semibold text-mukuru-navy">{s.label}</span>
                  </div>
                  <p className="text-xs text-mukuru-gray line-clamp-2">{s.text}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Language note */}
          <div className="mt-4 card bg-mukuru-gray-light border-0">
            <p className="text-xs text-mukuru-gray">
              Results show in your current language:{" "}
              <strong className="text-mukuru-navy">{language.toUpperCase()}</strong>
              . Change it from the header.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
