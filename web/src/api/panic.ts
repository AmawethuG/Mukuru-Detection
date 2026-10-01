import { apiFetch } from "./client";

export const triggerPanic = () =>
  apiFetch<{ status: string }>("/panic", { method: "POST", body: "{}" });
