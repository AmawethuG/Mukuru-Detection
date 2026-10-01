import { create } from "zustand";

export interface User {
  id: string;
  phone: string;
  country: string;
  language: string;
  created_at: string;
}

interface AppState {
  token: string | null;
  user: User | null;
  language: string;
  isDuress: boolean;
  setToken: (t: string) => void;
  setUser: (u: User) => void;
  setLanguage: (l: string) => void;
  setDuress: (d: boolean) => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  token: localStorage.getItem("token"),
  user: null,
  language: localStorage.getItem("language") ?? "en",
  isDuress: false,

  setToken: (t) => set({ token: t }),
  setUser: (u) => set({ user: u }),
  setLanguage: (l) => set({ language: l }),
  setDuress: (d) => set({ isDuress: d }),
  logout: () => {
    localStorage.removeItem("token");
    set({ token: null, user: null, isDuress: false });
  },
}));

// Persist token and language to localStorage whenever they change
useStore.subscribe((state) => {
  if (state.token) {
    localStorage.setItem("token", state.token);
  } else {
    localStorage.removeItem("token");
  }
  localStorage.setItem("language", state.language);
});
