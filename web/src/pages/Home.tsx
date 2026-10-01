import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../store/useStore";
import { postPanic } from "../api/panic";
import { t } from "../i18n";

export default function Home() {
  const lang = useStore((s) => s.language);
  const user = useStore((s) => s.user);
  const setDuress = useStore((s) => s.setDuress);
  const navigate = useNavigate();

  const [showPanicModal, setShowPanicModal] = useState(false);
  const [isPanicking, setIsPanicking] = useState(false);

  async function handlePanicConfirm(): Promise<void> {
    setIsPanicking(true);
    try {
      await postPanic();
      setDuress(true);
      setShowPanicModal(false);
      navigate("/history");
    } catch {
      // Still activate duress locally even if API fails
      setDuress(true);
      setShowPanicModal(false);
      navigate("/history");
    } finally {
      setIsPanicking(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-1">{t("app.name", lang)}</h1>
      <p className="text-gray-500 mb-8">
        Welcome, {user?.phone ?? ""}
      </p>

      {/* Quick-action cards */}
      <div className="grid grid-cols-2 gap-4">
        <Link
          to="/scan"
          className="block p-4 bg-white rounded-xl shadow hover:shadow-md text-center font-semibold text-gray-700 hover:text-blue-600 transition-shadow"
        >
          📱 {t("nav.scan", lang)}
        </Link>
        <Link
          to="/send"
          className="block p-4 bg-white rounded-xl shadow hover:shadow-md text-center font-semibold text-gray-700 hover:text-blue-600 transition-shadow"
        >
          💸 {t("nav.send", lang)}
        </Link>
        <Link
          to="/ussd"
          className="block p-4 bg-white rounded-xl shadow hover:shadow-md text-center font-semibold text-gray-700 hover:text-blue-600 transition-shadow"
        >
          📟 {t("nav.ussd", lang)}
        </Link>
        <Link
          to="/learn"
          className="block p-4 bg-white rounded-xl shadow hover:shadow-md text-center font-semibold text-gray-700 hover:text-blue-600 transition-shadow"
        >
          📚 {t("nav.learn", lang)}
        </Link>
      </div>

      {/* Panic button */}
      <button
        onClick={() => setShowPanicModal(true)}
        aria-label={t("panic.button_label", lang)}
        className="fixed bottom-20 right-4 md:bottom-4 bg-red-600 text-white rounded-full px-4 py-2 shadow-lg hover:bg-red-700 font-medium text-sm z-50"
      >
        {t("panic.button_label", lang)}
      </button>

      {/* Panic confirmation modal */}
      {showPanicModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="panic-modal-title"
        >
          <div className="bg-white rounded-xl p-6 max-w-sm w-full space-y-4">
            <h2 id="panic-modal-title" className="text-lg font-bold text-red-700">
              {t("panic.confirm.title", lang)}
            </h2>
            <p className="text-gray-600 text-sm">{t("panic.confirm.body", lang)}</p>
            <div className="flex gap-3">
              <button
                onClick={handlePanicConfirm}
                disabled={isPanicking}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 disabled:opacity-50"
              >
                {t("panic.confirm.yes", lang)}
              </button>
              <button
                onClick={() => setShowPanicModal(false)}
                className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                {t("panic.confirm.no", lang)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
