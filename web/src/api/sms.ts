import { apiFetch } from "./client";

export interface SMSMessage {
  id: string;
  direction: "inbound" | "outbound";
  sender: string;
  body: string;
  created_at: string;
}

export interface SMSOutboxResponse {
  messages: SMSMessage[];
  total: number;
  limit: number;
  offset: number;
}

export const getSmsOutbox = () => apiFetch<SMSOutboxResponse>("/sms/outbox");

export const sendSmsInbound = (from: string, body: string) =>
  apiFetch<{ status: string; reply: string }>("/sms/inbound", {
    method: "POST",
    body: JSON.stringify({ from, body }),
  });
