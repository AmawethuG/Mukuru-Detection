// Runtime i18n loader — reads JSON files from web/public/i18n/ via fetch
// Languages available: en, zu, fr, sw, st, hi, nl, pt

const cache: Record<string, Record<string, string>> = {};

/** Lazy-load a language file. Safe to call multiple times. */
export async function loadLanguage(lang: string): Promise<void> {
  if (cache[lang]) return;
  try {
    const res = await fetch(`/i18n/${lang}.json`);
    if (!res.ok) throw new Error(`Failed to load ${lang}`);
    const data = await res.json();
    cache[lang] = data as Record<string, string>;
  } catch {
    // Silently fall back; t() will use 'en'
  }
}

/** Translate a key. Falls back to 'en', then returns the key itself. */
export function t(key: string, lang: string): string {
  return cache[lang]?.[key] ?? cache["en"]?.[key] ?? key;
}

// Pre-load English on module import
loadLanguage("en");

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zu", label: "isiZulu" },
  { code: "fr", label: "Français" },
  { code: "sw", label: "Kiswahili" },
  { code: "st", label: "Sesotho" },
  { code: "hi", label: "हिन्दी" },
  { code: "nl", label: "Nederlands" },
  { code: "pt", label: "Português" },
] as const;
