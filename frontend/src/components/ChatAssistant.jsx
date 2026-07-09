import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage, addUserMessage } from "../store/slices/chatSlice";

const TOOL_LABELS = {
  log_interaction: "🗒 Logged interaction",
  edit_interaction: "✏️ Edited interaction",
  search_interactions: "🔍 Searched history",
  schedule_follow_up: "📅 Scheduled follow-up",
  get_hcp_insights: "💡 Generated insights",
};

const QUICK_PROMPTS = [
  'Met Dr. Emily Smith today, discussed Product X efficacy, she was positive, left a brochure and 2 samples of OncoBoost.',
  "What's the next best action for Dr. Emily Smith?",
  "Show my recent interactions with Dr. Emily Smith",
];

export default function ChatAssistant() {
  const dispatch = useDispatch();
  const { messages, sending, llmEnabled } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const submit = (text) => {
    const msg = (text ?? input).trim();
    if (!msg || sending) return;
    dispatch(addUserMessage(msg));
    dispatch(sendMessage(msg));
    setInput("");
  };

  return (
    <aside className="card chat-card">
      <header className="card-header chat-header">
        <div>
          <h2>🤖 AI Assistant</h2>
          <p className="chat-sub">Log interaction via chat</p>
        </div>
        {!llmEnabled && <span className="badge-warn">LLM off</span>}
      </header>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div className="bubble-text">{m.content}</div>
            {m.events && m.events.length > 0 && (
              <div className="bubble-events">
                {m.events.map((ev, j) => (
                  <span className="event-pill" key={j}>
                    {TOOL_LABELS[ev.tool] || ev.tool}
                    {ev.result?.id ? ` #${ev.result.id}` : ""}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="bubble assistant">
            <div className="typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      {messages.length <= 1 && (
        <div className="quick-prompts">
          {QUICK_PROMPTS.map((p, i) => (
            <button key={i} type="button" onClick={() => submit(p)}>
              {p.length > 46 ? p.slice(0, 46) + "…" : p}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input">
        <input
          type="text"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button
          type="button"
          className="btn-primary"
          disabled={sending || !input.trim()}
          onClick={() => submit()}
        >
          {sending ? "..." : "Log"}
        </button>
      </div>
    </aside>
  );
}
