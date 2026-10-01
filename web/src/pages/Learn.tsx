import { useEffect, useState } from "react";
import { getScamsLibrary, LibraryEntry } from "../api/library";
import { useStore } from "../store/useStore";
import { t } from "../i18n";

// Reason code → i18n key (mirrors ResultCard)
const REASON_KEYS: Record<string, string> = {
  FAKE_JOB_OFFER: "reason.fake_job_offer",
  ASKS_FOR_MONEY: "reason.asks_for_money",
  MOVE_TO_WHATSAPP: "reason.move_to_whatsapp",
  SUSPICIOUS_LINK: "reason.suspicious_link",
  REQUESTS_OTP_PIN: "reason.requests_otp_pin",
  URGENCY_LANGUAGE: "reason.urgency_language",
  IMPERSONATION: "reason.impersonation",
  ADVANCE_FEE: "reason.advance_fee",
  ROMANCE_SCAM: "reason.romance_scam",
  LOOKALIKE_DOMAIN: "reason.lookalike_domain",
  SHORTENED_URL: "reason.shortened_url",
  PHONE_IN_MESSAGE: "reason.phone_in_message",
  GENERIC_GREETING: "reason.generic_greeting",
  EMAIL_MISMATCH: "reason.email_mismatch",
  DISPLAY_NAME_SPOOF: "reason.display_name_spoof",
};

export default function Learn() {
  const lang = useStore((s) => s.language);

  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [category, setCategory] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load(): Promise<void> {
      setIsLoading(true);
      try {
        const res = await getScamsLibrary({
          lang,
          ...(category ? { category } : {}),
        });
        setEntries(res.entries);
      } catch {
        setError(t("common.error", lang));
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [lang, category]);

  const categories = [...new Set(entries.map((e) => e.category))];

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">{t("learn.title", lang)}</h1>
      <p className="text-gray-500 mb-6">{t("learn.subtitle", lang)}</p>

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="mb-6">
          <label htmlFor="learn-category" className="block text-sm font-medium text-gray-700 mb-1">
            {t("learn.category.label", lang)}
          </label>
          <select
            id="learn-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            <option value="">{t("common.unknown", lang)}</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {t(`category.${c}`, lang)}
              </option>
            ))}
          </select>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center mt-8">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : error ? (
        <p className="text-red-600 text-center">{error}</p>
      ) : entries.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          {t("learn.no_entries", lang)}
        </p>
      ) : (
        <div className="space-y-6">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="bg-white rounded-xl shadow p-5 space-y-3"
            >
              <h2 className="font-bold text-gray-800">
                {t(`category.${entry.category}`, lang)}
              </h2>

              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  {t("learn.example.label", lang)}
                </p>
                <blockquote className="border-l-4 border-yellow-400 pl-3 text-sm text-gray-600 italic">
                  {entry.example_message}
                </blockquote>
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  {t("learn.red_flags.label", lang)}
                </p>
                <ul className="list-disc list-inside space-y-1">
                  {entry.red_flags.map((flag) => (
                    <li key={flag} className="text-sm text-gray-700">
                      {t(REASON_KEYS[flag] ?? flag, lang)}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
