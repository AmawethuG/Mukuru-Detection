import { Link, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { useStore } from "../store/useStore";
import { loadLanguage } from "../i18n";
import { updateLanguage } from "../api/auth";
import { triggerPanic } from "../api/panic";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zu", label: "isiZulu" },
  { code: "fr", label: "Français" },
  { code: "sw", label: "Kiswahili" },
  { code: "st", label: "Sesotho" },
  { code: "hi", label: "हिन्दी" },
  { code: "nl", label: "Nederlands" },
  { code: "pt", label: "Português" },
];

/** Top navigation bar — mirrors the Mukuru.com header */
export function Header() {
  const { token, user, language, setLanguage, logout, setDuress } = useStore();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [panicOpen, setPanicOpen] = useState(false);

  async function handleLanguageChange(code: string) {
    await loadLanguage(code);
    setLanguage(code);
    if (token) await updateLanguage(code).catch(() => {});
    setLangOpen(false);
  }

  async function handlePanic() {
    await triggerPanic().catch(() => {});
    setDuress(true);
    setPanicOpen(false);
    navigate("/history");
  }

  return (
    <>
      {/* Panic confirmation modal */}
      {panicOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl">
            <h2 className="text-xl font-bold text-mukuru-navy mb-2">
              Activate Emergency Mode
            </h2>
            <p className="text-mukuru-gray text-sm mb-6">
              This will switch to a safe decoy account showing R0.00. A silent
              alert will be sent to your trusted contact. Your real account is
              untouched.
            </p>
            <div className="flex gap-3">
              <button onClick={handlePanic} className="btn-primary flex-1">
                Activate
              </button>
              <button
                onClick={() => setPanicOpen(false)}
                className="btn-outline flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="bg-white border-b border-mukuru-gray-border sticky top-0 z-40">
        {/* Top bar (country selector strip like mukuru.com) */}
        <div className="bg-mukuru-navy text-white text-xs py-1.5 px-4 flex justify-end gap-4">
          <span className="opacity-70">
            Protecting your money since the hackathon 🛡️
          </span>
          {token && (
            <button
              onClick={() => setPanicOpen(true)}
              className="text-red-300 hover:text-red-100 font-medium transition-colors"
              aria-label="Safety options"
            >
              Safety Options
            </button>
          )}
        </div>

        {/* Main nav */}
        <div className="section flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            {/* Green shield + wordmark */}
            <div className="w-9 h-9 bg-mukuru-green rounded-lg flex items-center justify-center">
              <span className="text-white font-extrabold text-lg leading-none">
                M
              </span>
            </div>
            <div className="leading-none">
              <div className="text-mukuru-navy font-extrabold text-lg tracking-tight">
                Mukuru
              </div>
              <div className="text-mukuru-green text-[10px] font-semibold tracking-widest uppercase">
                Detection
              </div>
            </div>
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-1">
            <Link to="/scan" className="btn-ghost text-sm">
              Check a Message
            </Link>
            <Link to="/send" className="btn-ghost text-sm">
              Send Money
            </Link>
            <Link to="/learn" className="btn-ghost text-sm">
              Learn
            </Link>
            <Link to="/ussd" className="btn-ghost text-sm">
              USSD Simulator
            </Link>
            <Link to="/demo" className="btn-ghost text-sm">
              Demo
            </Link>
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Language picker */}
            <div className="relative">
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="btn-ghost text-sm flex items-center gap-1"
                aria-expanded={langOpen}
              >
                🌐{" "}
                <span className="hidden sm:inline">
                  {LANGUAGES.find((l) => l.code === language)?.label ??
                    "English"}
                </span>
                <span className="sm:hidden">
                  {language.toUpperCase()}
                </span>
              </button>
              {langOpen && (
                <div className="absolute right-0 mt-1 w-44 bg-white rounded-xl shadow-lg border border-mukuru-gray-border py-1 z-50">
                  {LANGUAGES.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => handleLanguageChange(l.code)}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-mukuru-gray-light transition-colors
                        ${language === l.code ? "text-mukuru-green font-semibold" : "text-mukuru-navy"}`}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {token ? (
              <div className="flex items-center gap-2">
                <Link to="/history" className="hidden sm:block text-sm text-mukuru-gray">
                  {user?.phone}
                </Link>
                <button
                  onClick={() => { logout(); navigate("/"); }}
                  className="btn-outline text-sm py-2 px-4"
                >
                  Log Out
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login" className="btn-outline text-sm py-2 px-4">
                  Log In
                </Link>
                <Link to="/register" className="btn-primary text-sm py-2 px-4">
                  Sign Up
                </Link>
              </div>
            )}

            {/* Mobile hamburger */}
            <button
              className="md:hidden btn-ghost p-2"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              {menuOpen ? "✕" : "☰"}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-mukuru-gray-border bg-white py-2 px-4 flex flex-col gap-1">
            <Link to="/scan" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>Check a Message</Link>
            <Link to="/send" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>Send Money</Link>
            <Link to="/learn" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>Learn</Link>
            <Link to="/ussd" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>USSD Simulator</Link>
            <Link to="/sms" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>SMS Simulator</Link>
            <Link to="/demo" className="btn-ghost text-sm text-left" onClick={() => setMenuOpen(false)}>Demo</Link>
          </div>
        )}
      </header>
    </>
  );
}

/** Bottom nav for mobile */
export function BottomNav() {
  const { pathname } = useLocation();
  const { token } = useStore();

  const items = [
    { to: "/scan", icon: "🔍", label: "Check" },
    { to: "/ussd", icon: "📱", label: "USSD" },
    { to: "/learn", icon: "📚", label: "Learn" },
    ...(token ? [{ to: "/history", icon: "💳", label: "Account" }] : []),
    { to: "/demo", icon: "⭐", label: "Demo" },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-mukuru-gray-border z-40">
      <div className="flex">
        {items.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`flex-1 flex flex-col items-center py-2 text-xs gap-0.5 transition-colors
              ${pathname === item.to
                ? "text-mukuru-green"
                : "text-mukuru-gray hover:text-mukuru-navy"
              }`}
          >
            <span className="text-xl leading-none">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}

/** Mukuru-branded footer */
export function Footer() {
  return (
    <footer className="bg-mukuru-navy text-white mt-16">
      <div className="section py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-mukuru-green rounded-lg flex items-center justify-center">
              <span className="text-white font-extrabold">M</span>
            </div>
            <span className="font-bold text-lg">Mukuru Detection</span>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">
            Protecting people sending and receiving money across borders from
            scams and fraud.
          </p>
          <p className="text-white/40 text-xs mt-3">
            A Mukuru SheHacks Challenge C project.
          </p>
        </div>

        <div>
          <h3 className="font-semibold text-sm uppercase tracking-wider text-white/70 mb-3">
            Detection Tools
          </h3>
          <ul className="space-y-2 text-sm text-white/60">
            <li><Link to="/scan" className="hover:text-white transition-colors">Check a Message</Link></li>
            <li><Link to="/send" className="hover:text-white transition-colors">Send Money Safely</Link></li>
            <li><Link to="/ussd" className="hover:text-white transition-colors">USSD Simulator</Link></li>
            <li><Link to="/sms" className="hover:text-white transition-colors">SMS Simulator</Link></li>
          </ul>
        </div>

        <div>
          <h3 className="font-semibold text-sm uppercase tracking-wider text-white/70 mb-3">
            Learn
          </h3>
          <ul className="space-y-2 text-sm text-white/60">
            <li><Link to="/learn" className="hover:text-white transition-colors">Scam Library</Link></li>
            <li><Link to="/login-guard" className="hover:text-white transition-colors">Login Guard</Link></li>
            <li><Link to="/demo" className="hover:text-white transition-colors">Demo Panel</Link></li>
          </ul>
        </div>

        <div>
          <h3 className="font-semibold text-sm uppercase tracking-wider text-white/70 mb-3">
            Mukuru.com
          </h3>
          <ul className="space-y-2 text-sm text-white/60">
            <li><a href="https://mukuru.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Send Money</a></li>
            <li><a href="https://mukuru.com/za/en/about-us/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">About Mukuru</a></li>
            <li><a href="https://mukuru.com/za/en/help/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Help & Support</a></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="section py-4 flex flex-col sm:flex-row justify-between items-center gap-2 text-white/40 text-xs">
          <p>© 2026 Mukuru Detection. Built for Mukuru SheHacks, Challenge C.</p>
          <p>Mukuru Financial Services (Pty) Ltd. FSP45517</p>
        </div>
      </div>
    </footer>
  );
}

/** Full page wrapper used by every route */
export function PageLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 pb-20 md:pb-0">{children}</main>
      <Footer />
      <BottomNav />
    </div>
  );
}
