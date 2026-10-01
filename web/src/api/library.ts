import { apiFetch } from "./client";

export interface LibraryEntry {
  id: string;
  category: string;
  example_message: string;
  red_flags: string[];
  red_flags_translated: string[];
  advice: string[];
}

export interface LibraryResponse {
  lang: string;
  entries: LibraryEntry[];
}

export const getLibrary = (lang = "en", category?: string) => {
  const params = new URLSearchParams({ lang });
  if (category) params.set("category", category);
  return apiFetch<LibraryResponse>(`/scams/library?${params}`);
};
