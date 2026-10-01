import { apiFetch } from "./client";

export interface LoginGuardResponse {
  status: string;
  checkin_question?: string;
  advice?: string[];
  explanation?: string;
}

export const postLoginGuardEvent = (event_type: string, answer?: string) =>
  apiFetch<LoginGuardResponse>("/login-guard/event", {
    method: "POST",
    body: JSON.stringify({ event_type, answer: answer ?? null }),
  });
