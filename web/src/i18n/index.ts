// i18n helper — loads /i18n/<lang>.json from the public folder at runtime.
// Falls back key-by-key to "en" if a string is missing in the requested language.

const cache: Record<string, Record<string, string>> = {};

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "zu", label: "isiZulu" },
  { code: "fr", label: "Français" },
  { code: "sw", label: "Kiswahili" },
  { code: "st", label: "Sesotho" },
  { code: "hi", label: "हिन्दी" },
  { code: "nl", label: "Nederlands" },
  { code: "pt", label: "Português" },
];

/** Load a language file into the cache. Safe to call multiple times. */
export async function loadLanguage(lang: string): Promise<void> {
  if (cache[lang]) return;
  try {
    const res = await fetch(`/i18n/${lang}.json`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    cache[lang] = await res.json();
  } catch {
    console.warn(`[i18n] Could not load ${lang}.json — falling back to en`);
    cache[lang] = {};
  }
}

/** Translate a key in the given language. Falls back to "en", then to the key itself. */
export function t(key: string, lang = "en"): string {
  return cache[lang]?.[key] ?? cache["en"]?.[key] ?? key;
}

// Pre-load English on module import (always needed as the fallback)
loadLanguage("en");
