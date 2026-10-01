import { useEffect, useState } from "react";
import { getSmsOutbox, postSmsInbound } from "../api/sms";
import { useStore } from "../store/useStore";
import PhoneFrame from "../components/PhoneFrame";

interface ChatMessage {
  id: string;
  direction: "inbound" | "outbound";
  body: string;
}

export default function SMSSimulator() {
  const user = useStore((s) => s.user);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputBody, setInputBody] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOutbox(): Promise<void> {
      try {
        const res = await getSmsOutbox({});
        setMessages(
          res.messages.map((m) => ({
            id: m.id,
            direction: m.direction,
            body: m.body,
          }))
        );
      } catch {
        setError("Could not load messages.");
      }
    }
    loadOutbox();
  }, []);

  async function handleSend(): Promise<void> {
    if (!inputBody.trim() || isLoading) return;
    const body = inputBody.trim();
    setInputBody("");
    setIsLoading(true);
    setError(null);

    // Optimistically add the outbound message
    const tempId = crypto.randomUUID();
    setMessages((prev) => [...prev, { id: tempId, direction: "outbound", body }]);

    try {
      const res = await postSmsInbound({
        from: user?.phone ?? "+27831234567",
        body,
        timestamp: new Date().toISOString(),
      });
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), direction: "inbound", body: res.reply },
      ]);
    } catch {
      setError("Cannot connect to server.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto px-4 py-8">
      <h1 className="text-xl font-bold text-center mb-4">SMS Simulator</h1>

      <PhoneFrame title="SMS Simulator">
        {/* Chat messages */}
        <div className="flex flex-col gap-2 pb-2">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[85%] px-2 py-1 rounded text-xs ${
                msg.direction === "outbound"
                  ? "self-end ml-auto bg-green-900 text-green-200"
                  : "self-start bg-gray-800 text-green-400"
              }`}
            >
              {msg.body}
            </div>
          ))}
          {isLoading && (
            <div className="self-start bg-gray-800 text-green-400 text-xs px-2 py-1 rounded">
              …
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="text-red-400 text-xs mt-2">⚠ {error}</div>
        )}

        {/* Input area */}
        <div className="flex items-center gap-1 border-t border-green-900 pt-2 mt-auto">
          <input
            type="text"
            value={inputBody}
            onChange={(e) => setInputBody(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type a message…"
            className="flex-1 bg-transparent text-green-400 font-mono text-xs focus:outline-none placeholder-green-900"
            aria-label="SMS message input"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !inputBody.trim()}
            aria-label="Send SMS"
            className="text-xs bg-gray-700 text-green-400 px-2 py-1 rounded hover:bg-gray-600 disabled:opacity-50"
          >
            SEND
          </button>
        </div>
      </PhoneFrame>
    </div>
  );
}
