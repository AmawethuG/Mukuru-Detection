// USSD endpoint returns plain text, not JSON — use bare fetch (no apiFetch wrapper)
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface UssdRequest {
  sessionId: string;
  serviceCode: string;
  phoneNumber: string;
  text: string;
}

/** POST to /ussd — returns raw "CON ..." or "END ..." string. */
export const postUssd = async (req: UssdRequest): Promise<string> => {
  const res = await fetch(`${BASE}/ussd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`USSD error: HTTP ${res.status}`);
  return res.text();
};
