import { apiFetch } from "./client";

export interface UssdRequest {
  sessionId: string;
  serviceCode: string;
  phoneNumber: string;
  text: string;
}

/** Returns raw CON/END prefixed string from the backend */
export const postUssd = async (req: UssdRequest): Promise<string> => {
  const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  // USSD endpoint returns plain text, not JSON
  const res = await fetch(`${BASE}/ussd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`USSD error: HTTP ${res.status}`);
  return res.text();
};
