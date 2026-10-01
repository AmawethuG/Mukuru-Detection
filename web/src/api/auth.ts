import { apiFetch } from "./client";
import type { User } from "../store/useStore";

export interface LoginResponse {
  token: string;
  user: User;
}

export interface AccountResponse {
  id: string;
  phone: string;
  country: string;
  language: string;
  balance: string;
  currency: string;
  recent_transactions: TransactionSummary[];
  created_at: string;
}

export interface TransactionSummary {
  id: string;
  recipient: string;
  amount: string;
  currency: string;
  direction: "sent" | "received";
  created_at: string;
}

export const login = (phone: string, pin: string) =>
  apiFetch<LoginResponse>("/login", {
    method: "POST",
    body: JSON.stringify({ phone, pin }),
  });

export const register = (data: {
  phone: string;
  country: string;
  language: string;
  pin: string;
  duress_pin: string;
  trusted_contact?: string;
}) =>
  apiFetch<LoginResponse>("/register", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getMe = () => apiFetch<AccountResponse>("/accounts/me");

export const updateLanguage = (language: string) =>
  apiFetch<{ language: string }>("/accounts/me", {
    method: "PATCH",
    body: JSON.stringify({ language }),
  });
