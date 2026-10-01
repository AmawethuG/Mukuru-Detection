import { useNavigate } from "react-router-dom";
import { postLogin } from "../api/auth";
import { useStore } from "../store/useStore";
import { t } from "../i18n";

const SAMPLE_SCAM_KEYS = [
  { key: "demo.sample_scams.fake_job", label: "Fake Job Offer" },
  { key: "demo.sample_scams.phishing", label: "Phishing" },
  { key: "demo.sample_scams.romance", label: "Romance Scam" },
  { key: "demo.sample_scams.advance_fee", label: "Advance Fee" },
  { key: "demo.sample_scams.impersonation", label: "Impersonation" },
] as const;

export default function Demo() {
  const lang = useStore((s) => s.language);
  const setToken = useStore((s) => s.setToken);
  const setUser = useStore((s) => s.setUser);
  const navigate = useNavigate();

  async function loginAs(phone: string, pin: string, name: string): Promise<void> {
    try {
      const res = await postLogin({ phone, pin });
      setToken(res.token);
      setUser(res.user);
      navigate("/home");
    } catch {
      alert(`Could not log in as ${name}. Is the backend running?`);
    }
  }

  function loadInScanner(text: string): void {
    navigate("/scan", { state: { text } });
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">{t("demo.title", lang)}</h1>
      <p className="text-gray-500 mb-8">{t("demo.subtitle", lang)}</p>

      {/* Demo users */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {[
          { name: "Blessing", phone: "+27831234567", pin: "1234", color: "blue" },
          { name: "Tendai", phone: "+263771234567", pin: "1234", color: "purple" },
        ].map((u) => (
          <div key={u.name} className="bg-white rounded-xl shadow p-4 space-y-2">
            <h2 className="font-bold text-gray-800">{u.name}</h2>
            <p className="text-sm text-gray-500">{u.phone}</p>
            <p className="text-xs text-gray-400">PIN: {u.pin}</p>
            <button
              onClick={() => loginAs(u.phone, u.pin, u.name)}
              className={`w-full py-2 rounded-lg text-sm font-semibold ${
                u.color === "blue"
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "bg-purple-600 text-white hover:bg-purple-700"
              }`}
            >
              {t("demo.login_as", lang).replace("{name}", u.name)}
            </button>
          </div>
        ))}
      </div>

      {/* Sample scam cards */}
      <h2 className="font-bold text-gray-700 mb-4">
        {t("demo.sample_scams.title", lang)}
      </h2>
      <div className="space-y-4">
        {SAMPLE_SCAM_KEYS.map(({ key, label }) => {
          const msgText = t(key, lang);
          return (
            <div key={key} className="bg-white rounded-xl shadow p-4 space-y-3">
              <h3 className="font-semibold text-gray-700 text-sm">{label}</h3>
              <p className="text-sm text-gray-600 italic">{msgText}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => navigator.clipboard.writeText(msgText)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200"
                >
                  Copy
                </button>
                <button
                  onClick={() => loadInScanner(msgText)}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
                >
                  {t("demo.sample_scams.load", lang)}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
