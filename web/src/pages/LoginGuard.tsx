import { useState } from "react";
import { postLoginGuardEvent } from "../api/loginGuard";
import { useStore } from "../store/useStore";
import { t } from "../i18n";

type Phase = "idle" | "awaiting_answer" | "done";

export default function LoginGuard() {
  const lang = useStore((s) => s.language);

  const [phase, setPhase] = useState<Phase>("idle");
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("");
  const [advice, setAdvice] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSimulate(): Promise<void> {
    setIsLoading(true);
    try {
      const res = await postLoginGuardEvent("dating_app_login");
      setQuestion(res.checkin_question ?? t("login_guard.checkin_question", lang));
      setPhase("awaiting_answer");
    } catch {
      setStatus(t("common.error", lang));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAnswer(answer: "yes" | "no"): Promise<void> {
    setIsLoading(true);
    try {
      const res = await postLoginGuardEvent("dating_app_login", answer);
      setStatus(res.status);
      setAdvice(res.advice ?? []);
      setPhase("done");
    } catch {
      setStatus(t("common.error", lang));
      setPhase("done");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">{t("login_guard.title", lang)}</h1>
      <p className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 mb-6">
        {t("login_guard.simulation_notice", lang)}
      </p>

      {phase === "idle" && (
        <button
          onClick={handleSimulate}
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? t("common.loading", lang) : t("login_guard.simulate_button", lang)}
        </button>
      )}

      {phase === "awaiting_answer" && (
        <div className="space-y-4">
          <p className="text-gray-800 font-medium">{question}</p>
          <div className="flex gap-3">
            <button
              onClick={() => handleAnswer("yes")}
              disabled={isLoading}
              className="px-6 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50"
            >
              {t("login_guard.checkin_yes", lang)}
            </button>
            <button
              onClick={() => handleAnswer("no")}
              disabled={isLoading}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50"
            >
              {t("login_guard.checkin_no", lang)}
            </button>
          </div>
        </div>
      )}

      {phase === "done" && (
        <div className="space-y-4">
          {status === "risk_raised" ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-2">
              <h2 className="font-bold text-red-800">
                {t("login_guard.yes_response.title", lang)}
              </h2>
              <p className="text-red-700 text-sm">
                {t("login_guard.yes_response.body", lang)}
              </p>
              {advice.length > 0 && (
                <ul className="list-disc list-inside space-y-1 mt-2">
                  {advice.map((code) => (
                    <li key={code} className="text-red-700 text-sm">
                      {code}
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-gray-600 text-sm mt-2">
                {t("login_guard.risk_raised", lang)}
              </p>
            </div>
          ) : (
            <p className="text-gray-700">{t("login_guard.no_response", lang)}</p>
          )}
          <button
            onClick={() => {
              setPhase("idle");
              setQuestion("");
              setStatus("");
              setAdvice([]);
            }}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
          >
            {t("common.back", lang)}
          </button>
        </div>
      )}
    </div>
  );
}
