import { NavLink, useNavigate } from "react-router-dom";
import { useStore } from "../store/useStore";
import { t } from "../i18n";
import LanguageSwitcher from "./LanguageSwitcher";

const MOBILE_LINKS = [
  { to: "/home", labelKey: "nav.home", icon: "🏠" },
  { to: "/scan", labelKey: "nav.scan", icon: "🔍" },
  { to: "/send", labelKey: "nav.send", icon: "💸" },
  { to: "/ussd", labelKey: "nav.ussd", icon: "📟" },
  { to: "/learn", labelKey: "nav.learn", icon: "📚" },
];

const SIDEBAR_LINKS = [
  { to: "/home", labelKey: "nav.home", icon: "🏠" },
  { to: "/scan", labelKey: "nav.scan", icon: "🔍" },
  { to: "/send", labelKey: "nav.send", icon: "💸" },
  { to: "/ussd", labelKey: "nav.ussd", icon: "📟" },
  { to: "/sms", labelKey: "nav.sms", icon: "💬" },
  { to: "/learn", labelKey: "nav.learn", icon: "📚" },
  { to: "/demo", labelKey: "nav.demo", icon: "🎯" },
  { to: "/login-guard", labelKey: "nav.login_guard", icon: "🛡" },
];

export default function Nav() {
  const lang = useStore((s) => s.language);
  const user = useStore((s) => s.user);
  const token = useStore((s) => s.token);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();

  function handleLogout(): void {
    logout();
    navigate("/login");
  }

  const activeCls = "bg-gray-700 text-white rounded-lg";
  const baseCls = "flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors";

  return (
    <>
      {/* Mobile bottom nav */}
      <nav
        aria-label="Mobile navigation"
        className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 flex justify-around items-center h-14 md:hidden"
      >
        {MOBILE_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-2 text-xs ${
                isActive ? "text-blue-600 font-semibold" : "text-gray-500"
              }`
            }
          >
            <span aria-hidden="true">{link.icon}</span>
            <span>{t(link.labelKey, lang)}</span>
          </NavLink>
        ))}
      </nav>

      {/* Desktop sidebar */}
      <aside
        aria-label="Sidebar navigation"
        className="hidden md:flex fixed left-0 top-0 h-full w-56 flex-col bg-gray-900 text-white p-4 gap-1 z-40"
      >
        <div className="mb-4">
          <h1 className="text-sm font-bold text-white tracking-wide">
            {t("app.name", lang)}
          </h1>
        </div>

        {SIDEBAR_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `${baseCls} ${isActive ? activeCls : ""}`
            }
          >
            <span aria-hidden="true">{link.icon}</span>
            {t(link.labelKey, lang)}
          </NavLink>
        ))}

        <div className="mt-auto space-y-2">
          {user && (
            <p className="text-xs text-gray-400 px-3">{user.phone}</p>
          )}
          <div className="px-1">
            <LanguageSwitcher />
          </div>
          {token && (
            <button
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
            >
              {t("nav.logout", lang)}
            </button>
          )}
        </div>
      </aside>

      {/* Desktop top header bar */}
      <header className="hidden md:flex fixed top-0 right-0 left-56 z-40 bg-white border-b border-gray-200 px-6 py-3 items-center justify-between h-14">
        <span className="font-semibold text-gray-700">{t("app.name", lang)}</span>
        <LanguageSwitcher />
      </header>
    </>
  );
}
