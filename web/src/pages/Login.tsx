import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useStore } from "../store/useStore";
import { loadLanguage } from "../i18n";

// Demo credentials shown in the "quick login" panel
const DEMO_USERS = [
  {
    label: "Blessing (isiZulu · South Africa)",
    phone: "+27831234567",
    pin: "1234",
    duress: "9999",
    flag: "🇿🇦",
  },
  {
    label: "Tendai (English · Zimbabwe)",
    phone: "+263771234567",
    pin: "1234",
    duress: "9999",
    flag: "🇿🇼",
  },
];

export default function Login() {
  const navigate = useNavigate();
  const { setToken, setUser } = useStore();

  const [phone, setPhone] = useState("");
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(phone, pin);
      localStorage.setItem("mukuru-token", res.token);
      setToken(res.token);
      setUser(res.user);
      await loadLanguage(res.user.language);
      navigate("/home");
    } catch (err: unknown) {
      const e = err as { status?: number };
      if (e.status === 429) {
        setError("Too many attempts. Please wait 5 minutes.");
      } else {
        setError("Incorrect phone number or PIN.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function quickLogin(demoPhone: string, demoPin: string) {
    setPhone(demoPhone);
    setPin(demoPin);
    setError("");
    setLoading(true);
    try {
      const res = await login(demoPhone, demoPin);
      localStorage.setItem("mukuru-token", res.token);
      setToken(res.token);
      setUser(res.user);
      await loadLanguage(res.user.language);
      navigate("/home");
    } catch {
      setError("Demo account not found. Run python backend/seed.py first.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-mukuru-gray-light flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md space-y-6">

        {/* Card */}
        <div className="card">
          {/* Logo */}
          <div className="flex items-center gap-2 mb-6">
            <div className="w-9 h-9 bg-mukuru-green rounded-lg flex items-center justify-center">
              <span className="text-white font-extrabold text-lg">M</span>
            </div>
            <div>
              <div className="font-extrabold text-mukuru-navy text-base leading-tight">Mukuru Detection</div>
              <div className="text-xs text-mukuru-gray">Log in to your account</div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">
                Phone number
              </label>
              <input
                type="tel"
                className="field"
                placeholder="+27831234567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
                autoComplete="tel"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">
                PIN
              </label>
              <input
                type="password"
                className="field tracking-[0.5em]"
                placeholder="••••"
                maxLength={4}
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))}
                required
                autoComplete="current-password"
                inputMode="numeric"
              />
            </div>

            {error && (
              <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5"
            >
              {loading ? "Logging in…" : "Log In"}
            </button>
          </form>

          <p className="text-center text-sm text-mukuru-gray mt-4">
            Don't have an account?{" "}
            <Link to="/register" className="text-mukuru-green font-semibold hover:underline">
              Register here
            </Link>
          </p>
        </div>

        {/* Demo quick-login panel */}
        <div className="card border-mukuru-green/30 bg-mukuru-green-light">
          <p className="text-xs font-semibold uppercase tracking-wider text-mukuru-green mb-3">
            ⭐ Demo accounts — one click login
          </p>
          <div className="space-y-2">
            {DEMO_USERS.map((u) => (
              <button
                key={u.phone}
                onClick={() => quickLogin(u.phone, u.pin)}
                disabled={loading}
                className="w-full text-left p-3 rounded-xl bg-white border border-mukuru-green/20
                           hover:border-mukuru-green hover:shadow-sm transition-all flex items-center gap-3"
              >
                <span className="text-2xl">{u.flag}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-mukuru-navy text-sm">{u.label}</div>
                  <div className="text-xs text-mukuru-gray">
                    {u.phone} · PIN: {u.pin} · Duress: {u.duress}
                  </div>
                </div>
                <span className="text-mukuru-green text-sm font-semibold shrink-0">Log in →</span>
              </button>
            ))}
          </div>
          <p className="text-xs text-mukuru-gray mt-3">
            Or use the duress PIN <strong>9999</strong> to see the panic decoy view.
          </p>
        </div>
      </div>
    </div>
  );
}
