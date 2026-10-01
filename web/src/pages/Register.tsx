import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { useStore } from "../store/useStore";
import { loadLanguage } from "../i18n";

const COUNTRIES = [
  { code: "ZA", name: "South Africa 🇿🇦", defaultLang: "zu" },
  { code: "ZW", name: "Zimbabwe 🇿🇼", defaultLang: "en" },
  { code: "MZ", name: "Mozambique 🇲🇿", defaultLang: "pt" },
  { code: "AO", name: "Angola 🇦🇴", defaultLang: "pt" },
  { code: "CD", name: "DR Congo 🇨🇩", defaultLang: "fr" },
  { code: "TZ", name: "Tanzania 🇹🇿", defaultLang: "sw" },
  { code: "KE", name: "Kenya 🇰🇪", defaultLang: "sw" },
  { code: "IN", name: "India 🇮🇳", defaultLang: "hi" },
  { code: "NL", name: "Netherlands 🇳🇱", defaultLang: "nl" },
  { code: "OTHER", name: "Other", defaultLang: "en" },
];

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "zu", name: "isiZulu" },
  { code: "fr", name: "Français" },
  { code: "sw", name: "Kiswahili" },
  { code: "st", name: "Sesotho" },
  { code: "hi", name: "हिन्दी" },
  { code: "nl", name: "Nederlands" },
  { code: "pt", name: "Português" },
];

export default function Register() {
  const navigate = useNavigate();
  const { setToken, setUser } = useStore();

  const [form, setForm] = useState({
    phone: "",
    country: "ZA",
    language: "zu",
    pin: "",
    pinConfirm: "",
    duress_pin: "",
    duressPinConfirm: "",
    trusted_contact: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function set(field: string, value: string) {
    setForm((f) => {
      const updated = { ...f, [field]: value };
      // Auto-set language when country changes
      if (field === "country") {
        const country = COUNTRIES.find((c) => c.code === value);
        if (country) updated.language = country.defaultLang;
      }
      return updated;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (form.pin !== form.pinConfirm) {
      setError("PINs do not match.");
      return;
    }
    if (form.duress_pin !== form.duressPinConfirm) {
      setError("Duress PINs do not match.");
      return;
    }
    if (form.pin === form.duress_pin) {
      setError("Your duress PIN must be different from your main PIN.");
      return;
    }
    if (form.pin.length !== 4 || form.duress_pin.length !== 4) {
      setError("PINs must be exactly 4 digits.");
      return;
    }

    setLoading(true);
    try {
      const res = await register({
        phone: form.phone,
        country: form.country,
        language: form.language,
        pin: form.pin,
        duress_pin: form.duress_pin,
        trusted_contact: form.trusted_contact || undefined,
      });
      localStorage.setItem("mukuru-token", res.token);
      setToken(res.token);
      setUser(res.user);
      await loadLanguage(res.user.language);
      navigate("/home");
    } catch (err: unknown) {
      const e = err as { status?: number; body?: { message?: string } };
      if (e.status === 409) setError("This phone number is already registered.");
      else setError(e.body?.message ?? "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-mukuru-gray-light flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-9 h-9 bg-mukuru-green rounded-lg flex items-center justify-center">
              <span className="text-white font-extrabold text-lg">M</span>
            </div>
            <div>
              <div className="font-extrabold text-mukuru-navy text-base leading-tight">Mukuru Detection</div>
              <div className="text-xs text-mukuru-gray">Create your account</div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Phone */}
            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">Phone number</label>
              <input
                type="tel"
                className="field"
                placeholder="+27831234567"
                value={form.phone}
                onChange={(e) => set("phone", e.target.value)}
                required
              />
            </div>

            {/* Country + Language in a row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">Country</label>
                <select
                  className="field"
                  value={form.country}
                  onChange={(e) => set("country", e.target.value)}
                >
                  {COUNTRIES.map((c) => (
                    <option key={c.code} value={c.code}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">Language</label>
                <select
                  className="field"
                  value={form.language}
                  onChange={(e) => set("language", e.target.value)}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* PIN */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">PIN</label>
                <input
                  type="password"
                  className="field tracking-[0.5em]"
                  placeholder="••••"
                  maxLength={4}
                  inputMode="numeric"
                  value={form.pin}
                  onChange={(e) => set("pin", e.target.value.replace(/\D/g, ""))}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-mukuru-navy mb-1">Confirm PIN</label>
                <input
                  type="password"
                  className="field tracking-[0.5em]"
                  placeholder="••••"
                  maxLength={4}
                  inputMode="numeric"
                  value={form.pinConfirm}
                  onChange={(e) => set("pinConfirm", e.target.value.replace(/\D/g, ""))}
                  required
                />
              </div>
            </div>

            {/* Duress PIN */}
            <div className="rounded-xl bg-mukuru-orange-light border border-orange-200 p-4 space-y-3">
              <div>
                <p className="text-sm font-semibold text-mukuru-navy">Duress PIN</p>
                <p className="text-xs text-mukuru-gray mt-0.5">
                  Enter this PIN if you're being forced to transact. It shows a safe decoy screen — your real account is untouched.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-mukuru-navy mb-1">Duress PIN</label>
                  <input
                    type="password"
                    className="field tracking-[0.5em]"
                    placeholder="••••"
                    maxLength={4}
                    inputMode="numeric"
                    value={form.duress_pin}
                    onChange={(e) => set("duress_pin", e.target.value.replace(/\D/g, ""))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-mukuru-navy mb-1">Confirm</label>
                  <input
                    type="password"
                    className="field tracking-[0.5em]"
                    placeholder="••••"
                    maxLength={4}
                    inputMode="numeric"
                    value={form.duressPinConfirm}
                    onChange={(e) => set("duressPinConfirm", e.target.value.replace(/\D/g, ""))}
                    required
                  />
                </div>
              </div>
            </div>

            {/* Optional trusted contact */}
            <div>
              <label className="block text-sm font-medium text-mukuru-navy mb-1">
                Trusted contact <span className="text-mukuru-gray font-normal">(optional)</span>
              </label>
              <input
                type="tel"
                className="field"
                placeholder="+27821234567 — alerted if you use panic mode"
                value={form.trusted_contact}
                onChange={(e) => set("trusted_contact", e.target.value)}
              />
            </div>

            {error && (
              <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full py-3.5">
              {loading ? "Creating account…" : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-mukuru-gray mt-4">
            Already have an account?{" "}
            <Link to="/login" className="text-mukuru-green font-semibold hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
