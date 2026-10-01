import { apiFetch } from "./client";

export type Channel = "web" | "sms" | "email" | "ussd";
export type Tier = "SAFE" | "CAUTION" | "HIGH_RISK";

export interface ScanResponse {
  id: string;
  score: number;
  tier: Tier;
  category: string;
  reasons: string[];
  advice: string[];
  explanation: string;
  explanation_source: "rules" | "llm";
  detected_language: string;
  scanned_at: string;
}

export const scanMessage = (text: string, channel: Channel, user_id?: string) =>
  apiFetch<ScanResponse>("/scan", {
    method: "POST",
    body: JSON.stringify({ text, channel, user_id }),
  });
