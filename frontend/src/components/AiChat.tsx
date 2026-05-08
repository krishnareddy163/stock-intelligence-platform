"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, TrendingUp } from "lucide-react";
import { aiApi, ChatMessage } from "@/services/api";
import { clsx } from "clsx";

const SUGGESTIONS = [
  "Best Nifty 50 stocks for 2025?",
  "Build a ₹1L growth portfolio",
  "Is RELIANCE a good buy now?",
  "Compare TCS vs Infosys",
];

export default function AiChat({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Namaste! I'm your AI advisor for Indian stock markets.\n\nAsk me about NSE/BSE stocks, portfolio strategy, or market analysis.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = { role: "user", content };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      const res = await aiApi.chat(content, userId, messages.slice(-10));
      setMessages([
        ...newHistory,
        { role: "assistant", content: res.data.response || "I couldn't generate a response. Please try again." },
      ]);
    } catch {
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content:
            "AI orchestrator isn't running yet.\n\nStart it with:\ndocker compose up -d ai-orchestrator",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded border border-gray-200 shadow-sm overflow-hidden">

      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 py-3 border-b border-gray-200 bg-[#f0fdf4]">
        <div className="w-8 h-8 rounded bg-[#166534] flex items-center justify-center shadow-sm">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-[#166534] leading-none">AI Stock Advisor</p>
          <p className="text-[10px] text-gray-500 mt-0.5">Claude + MCP · NSE/BSE</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] text-gray-500">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-gray-50">
        {messages.map((msg, i) => (
          <div key={i} className={clsx("flex gap-2", msg.role === "user" ? "flex-row-reverse" : "")}>
            <div
              className={clsx(
                "w-7 h-7 rounded flex items-center justify-center shrink-0 mt-0.5",
                msg.role === "user" ? "bg-[#166534]" : "bg-white border border-gray-200 shadow-sm"
              )}
            >
              {msg.role === "user" ? (
                <User className="w-3.5 h-3.5 text-white" />
              ) : (
                <TrendingUp className="w-3.5 h-3.5 text-[#166534]" />
              )}
            </div>
            <div
              className={clsx(
                "max-w-[82%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap shadow-sm",
                msg.role === "user"
                  ? "bg-[#166534] text-white rounded-tr-sm"
                  : "bg-white text-gray-700 border border-gray-200 rounded-tl-sm"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Typing dots */}
        {loading && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded bg-white border border-gray-200 shadow-sm flex items-center justify-center shrink-0">
              <TrendingUp className="w-3.5 h-3.5 text-[#166534]" />
            </div>
            <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-4 py-3 flex items-center gap-1 shadow-sm">
              {[0, 150, 300].map((d) => (
                <span
                  key={d}
                  className="w-1.5 h-1.5 bg-[#166534] rounded-full animate-bounce"
                  style={{ animationDelay: `${d}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Suggestion chips */}
        {messages.length === 1 && !loading && (
          <div className="pt-1 space-y-2">
            <p className="text-[10px] text-gray-400 uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Try asking
            </p>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs px-2.5 py-1.5 rounded-lg bg-white border border-gray-200 hover:border-[#166534] hover:text-[#166534] text-gray-600 transition-all shadow-sm"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-2.5 border-t border-gray-200 flex gap-2 bg-white">
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask about Nifty stocks…"
          className="flex-1 border border-gray-300 text-gray-800 rounded-lg px-3 py-2 text-sm outline-none focus:border-[#166534] transition-colors placeholder-gray-400 bg-white"
        />
        <button
          aria-label="Send"
          onClick={() => send()}
          disabled={loading || !input.trim()}
          className="w-9 h-9 rounded-lg bg-[#166534] hover:bg-[#15803d] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
        >
          <Send className="w-3.5 h-3.5 text-white" />
        </button>
      </div>
    </div>
  );
}
