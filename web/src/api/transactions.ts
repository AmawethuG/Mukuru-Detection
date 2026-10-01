import { apiFetch } from "./client";
import type { Tier } from "./scan";

export interface TxnCheckResponse {
  score: number;
  tier: Tier;
  reasons: string[];
  advice: string[];
  checked_at: string;
}

export interface SendResponse {
  transaction_id: string;
  status: string;
  amount: string;
  currency: string;
  recipient: string;
  sent_at: string;
}

export interface Transaction {
  id: string;
  recipient: string;
  amount: string;
  currency: string;
  direction: "sent" | "received";
  country?: string;
  status: string;
  created_at: string;
}

export interface HistoryResponse {
  transactions: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export const checkTransaction = (data: {
  recipient: string;
  amount: string;
  currency: string;
  country: string;
}) =>
  apiFetch<TxnCheckResponse>("/transactions/check", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const sendMoney = (data: {
  recipient: string;
  amount: string;
  currency: string;
  country: string;
  force?: boolean;
}) =>
  apiFetch<SendResponse>("/transactions/send", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getHistory = (limit = 20, offset = 0) =>
  apiFetch<HistoryResponse>(`/transactions/history?limit=${limit}&offset=${offset}`);
