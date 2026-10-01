import { useState } from "react";
import {
  checkTransaction,
  sendMoney,
  type TxnCheckResponse,
  type SendResponse,
} from "../api/transactions";
import { ResultCard } from "../components/ResultCard";
import { useStore } from "../store/useStore";
import { t } from "../i18n";

const CURRENCIES = ["ZAR", "USD", "ZWL", "MZN", "EUR"];
const COUNTRIES = [
  { code: "ZA", name: "South Africa 🇿🇦" },
  { code: "ZW", name: "Zimbabwe 🇿🇼" },
  { code: "MZ", name: "Mozambique 🇲🇿" },
  { code: "AO", name: "Angola 🇦🇴" },
  { code: "CD", name: "DR Congo 🇨🇩" },
  { code: "TZ", name: "Tanzania 🇹🇿" },
  { code: "KE", name: "Kenya 🇰🇪" },
  { code: "OTHER", name: "Other" },
];

type Step = "form" | "checking" | "warning" | "sending" | "success" | "error";

export default function Send() {
  const { language } = useStore();

  const [form, setForm] = useState({
    recipient: "",
    amount: "",
    currency: "ZAR",
    country: "ZW",
  });
  const [step, setStep] = useState<Step>("form");
  const [checkResult, setCheckResult] = useState<TxnCheckResponse | null>(null);
  const [sendResult, setSendResult] = useState<SendResponse | null>(null);
  const [error, setError] = useState("");

  function setField(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleCheck(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setStep("checking");
    try {
      const res = await checkTransaction(form);
      setCheckResult(res);
      if (res.tier === "SAFE") {
        // No warning needed — proceed directly to send
        await doSend(false);
      } else {
        setStep("warning");
      }
    } catch {
      setError("Could not run risk check. Make sure the backend is running.");
      setStep("error");
    }
  }

  async function doSend(force: boolean) {
    setStep("sending");
    try {
      const res = await sendMoney({ ...form, force });
      setSendResult(res);
      setStep("success");
    } catch (err: unknown) {
      const e = err as { status?: number };
      if (e.status === 422) {
        setStep("warning"); // Already showing the warning card
      } else {
        setError("Transfer failed. Please try again.");
        setStep("error");
      }
    }
  }

  function reset() {
    setForm({ recipient: "", amount: "", currency: "ZAR", country: "ZW" });
    setStep("form");
    setCheckResult(null);
    setSendResult(null);
    setError("");
  }

  return (
    <div className="section py-10">
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-extrabold text-mukuru-navy mb-1">
          Send Money
        </h1>
        <p className="text-mukuru-gray">
          We check every transfer for risk signals before you send.
        </p>
      </div>

      <div className="max-w-lg mx-auto space-y-6">

        {/* ── Form ─────────────────────────────────────────────────── */}
        {(step === "form" || step === "checking") && (
          <form onSubmit={handleCheck} className="card space-y-4">
            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">
                Recipient (phone or account)
              </label>
              <input
                type="text"
                className="field"
                placeholder="+263771234567"
                value={form.recipient}
                onChange={(e) => setField("recipient", e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">Amount</label>
                <input
                  type="number"
                  className="field"
                  placeholder="500"
                  min="1"
                  step="0.01"
                  value={form.amount}
                  onChange={(e) => setField("amount", e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">Currency</label>
                <select className="field" value={form.currency} onChange={(e) => setField("currency", e.target.value)}>
                  {CURRENCIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">
                Destination country
              </label>
              <select className="field" value={form.country} onChange={(e) => setField("country", e.target.value)}>
                {COUNTRIES.map((c) => (
                  <option key={c.code} value={c.code}>{c.name}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={step === "checking"}
              className="btn-primary w-full py-3.5"
            >
              {step === "checking" ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  Checking transfer…
                </span>
              ) : (
                "Check & Send →"
              )}
            </button>
          </form>
        )}

        {/* ── Risk warning ─────────────────────────────────────────── */}
        {step === "warning" && checkResult && (
          <div className="space-y-4">
            <ResultCard
              tier={checkResult.tier}
              score={checkResult.score}
              category="unknown"
              reasons={checkResult.reasons}
              advice={checkResult.advice}
              lang={language}
            />

            {/* Transfer summary */}
            <div className="card bg-mukuru-gray-light border-0">
              <p className="text-sm font-medium text-mukuru-navy mb-1">Transfer details</p>
              <div className="text-sm text-mukuru-gray space-y-0.5">
                <div>To: <strong className="text-mukuru-navy">{form.recipient}</strong></div>
                <div>Amount: <strong className="text-mukuru-navy">{form.amount} {form.currency}</strong></div>
                <div>Country: <strong className="text-mukuru-navy">{COUNTRIES.find(c=>c.code===form.country)?.name}</strong></div>
              </div>
            </div>

            {/* Warning action — uses i18n keys */}
            <div className="flex gap-3">
              <button
                onClick={reset}
                className="btn-primary flex-1 py-3"
              >
                {t("send.warning.pause", language)}
              </button>
              <button
                onClick={() => doSend(true)}
                className="btn-outline flex-1 py-3 border-mukuru-gray text-mukuru-gray hover:bg-gray-50"
              >
                {t("send.warning.send_anyway", language)}
              </button>
            </div>
          </div>
        )}

        {/* ── Sending ───────────────────────────────────────────────── */}
        {step === "sending" && (
          <div className="card text-center py-10">
            <svg className="animate-spin h-8 w-8 text-mukuru-green mx-auto mb-3" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            <p className="text-mukuru-gray font-medium">Processing transfer…</p>
          </div>
        )}

        {/* ── Success ──────────────────────────────────────────────── */}
        {step === "success" && sendResult && (
          <div className="card border-green-200 bg-green-50 text-center py-8 space-y-3">
            <div className="text-4xl">✅</div>
            <h2 className="text-xl font-bold text-green-800">
              {t("send.success", language)}
            </h2>
            <div className="text-sm text-green-700 space-y-1">
              <p>Amount: <strong>{sendResult.amount} {sendResult.currency}</strong></p>
              <p>To: <strong>{sendResult.recipient}</strong></p>
              <p className="text-xs text-green-600">
                Ref: {sendResult.transaction_id.slice(0, 8).toUpperCase()}
              </p>
            </div>
            <button onClick={reset} className="btn-primary mt-2">
              Send another
            </button>
          </div>
        )}

        {/* ── Error ────────────────────────────────────────────────── */}
        {step === "error" && (
          <div className="card border-red-200 bg-red-50 text-center py-8 space-y-3">
            <div className="text-4xl">⚠️</div>
            <p className="text-red-700 font-medium">{error}</p>
            <button onClick={reset} className="btn-outline border-red-400 text-red-700 hover:bg-red-50">
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
