import { useStore } from "../store/useStore";
import { SUPPORTED_LANGUAGES, loadLanguage } from "../i18n";

export default function LanguageSwitcher() {
  const language = useStore((s) => s.language);
  const setLanguage = useStore((s) => s.setLanguage);

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const newLang = e.target.value;
    setLanguage(newLang);
    loadLanguage(newLang);
  }

  return (
    <div className="flex items-center gap-1">
      <label htmlFor="lang-select" className="sr-only">
        Select language
      </label>
      <select
        id="lang-select"
        value={language}
        onChange={handleChange}
        className="border border-gray-300 rounded px-2 py-1 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
      >
        {SUPPORTED_LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </div>
  );
}
