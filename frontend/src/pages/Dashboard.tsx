"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Search, TrendingUp, TrendingDown, RefreshCw, Loader2,
  AlertCircle, Zap, WifiOff, Bot, BarChart2,
  ArrowUpRight, ArrowDownRight, Filter,
} from "lucide-react";
import AiChat from "@/components/AiChat";
import { recommendationApi, AnalysisRequest } from "@/services/api";
import { clsx } from "clsx";

const MARKETS = [
  { label: "Nifty 50",  flag: "🇮🇳", country: "IN", index: "NIFTY50" },
  { label: "Nifty 500", flag: "🇮🇳", country: "IN", index: "NIFTY500" },
  { label: "Sensex",    flag: "🇮🇳", country: "IN", index: "SENSEX" },
  { label: "BSE 500",   flag: "🇮🇳", country: "IN", index: "BSE500" },
  { label: "NASDAQ",    flag: "🇺🇸", country: "US", index: "NASDAQ" },
  { label: "S&P 500",   flag: "🇺🇸", country: "US", index: "SP500" },
];

const INDICES = [
  { name: "NIFTY 50",     value: "22,475.85", change: "+142.50", pct: "+0.64%", up: true  },
  { name: "SENSEX",       value: "73,961.32", change: "+385.97", pct: "+0.52%", up: true  },
  { name: "BANK NIFTY",   value: "48,201.05", change: "-203.45", pct: "-0.42%", up: false },
  { name: "NIFTY IT",     value: "35,102.80", change: "+312.10", pct: "+0.90%", up: true  },
  { name: "NIFTY MIDCAP", value: "13,847.20", change: "+87.30",  pct: "+0.63%", up: true  },
  { name: "GOLD",         value: "₹71,450",   change: "+125",    pct: "+0.18%", up: true  },
];

const RISK_PROFILES = [
  { key: "LOW",    label: "Conservative", dot: "bg-emerald-500" },
  { key: "MEDIUM", label: "Moderate",     dot: "bg-amber-500"   },
  { key: "HIGH",   label: "Aggressive",   dot: "bg-red-500"     },
];

const HORIZONS = [
  { key: "SHORT_TERM", label: "Short Term", sub: "< 3M" },
  { key: "MID_TERM",   label: "Mid Term",   sub: "3–12M" },
  { key: "LONG_TERM",  label: "Long Term",  sub: "> 1Y" },
];

const STRATEGIES = [
  { key: "GROWTH",   label: "Growth"   },
  { key: "VALUE",    label: "Value"    },
  { key: "DIVIDEND", label: "Dividend" },
  { key: "MOMENTUM", label: "Momentum" },
  { key: "HYBRID",   label: "Hybrid"   },
];

const ACTION_CFG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  STRONG_BUY:  { label: "Strong Buy",  color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-300" },
  BUY:         { label: "Buy",         color: "text-green-700",   bg: "bg-green-50",   border: "border-green-300"   },
  HOLD:        { label: "Hold",        color: "text-amber-700",   bg: "bg-amber-50",   border: "border-amber-300"   },
  SELL:        { label: "Sell",        color: "text-red-700",     bg: "bg-red-50",     border: "border-red-300"     },
  STRONG_SELL: { label: "Strong Sell", color: "text-rose-700",    bg: "bg-rose-50",    border: "border-rose-300"    },
};

const SIDEBAR_SECTION = "bg-white rounded border border-gray-200 overflow-hidden";
const SIDEBAR_HEADER  = "px-3 py-2 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide";
const SIDEBAR_ITEM    = "w-full flex items-center gap-2 px-2.5 py-1.5 rounded text-sm transition-colors text-left";

export default function Dashboard() {
  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("userId") || "demo-user"
      : "demo-user";

  const [form, setForm] = useState<AnalysisRequest>({
    userId,
    query: "Find the best Indian stocks with strong growth potential",
    country: "IN",
    index: "NIFTY50",
    investmentAmount: 100000,
    riskProfile: "MEDIUM",
    timeHorizon: "LONG_TERM",
    strategy: "GROWTH",
    preferredSectors: [],
  });

  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"signals" | "analysis">("signals");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const analyzeMutation = useMutation({
    mutationFn: () => recommendationApi.analyze(form),
    onSuccess: (res) => {
      setErrorMsg(null);
      setAnalysisResult(res.data.analysis);
      const toolCalls = res.data.toolCalls || [];
      const signalCall = toolCalls.find((t: any) => t.tool === "generate_buy_sell_signals");
      if (signalCall?.output?.signals) {
        setSignals(signalCall.output.signals);
        setActiveTab("signals");
      } else {
        setActiveTab("analysis");
      }
    },
    onError: (err: any) => {
      setErrorMsg(!err.response ? "backend_down" : err.response?.data?.message || "Analysis failed.");
    },
  });

  const set = (key: keyof AnalysisRequest, val: any) =>
    setForm((p) => ({ ...p, [key]: val }));

  const currency = form.country === "IN" ? "₹" : "$";
  const selectedMarket = MARKETS.find((m) => m.index === form.index);

  const quickAmounts =
    form.country === "IN"
      ? [{ v: 25000, label: "₹25K" }, { v: 100000, label: "₹1L" }, { v: 500000, label: "₹5L" }]
      : [{ v: 5000, label: "$5K" }, { v: 10000, label: "$10K" }, { v: 50000, label: "$50K" }];

  return (
    <div className="min-h-screen bg-[#f5f7fa] text-[#1e293b]">

      {/* ── Header ── */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-[1600px] mx-auto px-4 h-12 flex items-center gap-4">
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded bg-[#166534] flex items-center justify-center">
              <BarChart2 className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-[#166534] text-lg tracking-tight">StockIQ</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0] font-semibold">
              AI
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-5 ml-4">
            {["Screener", "Portfolio", "Watchlist", "IPO", "News"].map((n) => (
              <a
                key={n}
                href="#"
                className={clsx(
                  "text-sm font-medium transition-colors",
                  n === "Screener" ? "text-[#166534]" : "text-gray-500 hover:text-gray-800"
                )}
              >
                {n}
              </a>
            ))}
          </nav>

          <div className="flex-1 max-w-md mx-4 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search stocks, e.g. Reliance, TCS, Infosys…"
              className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-300 rounded bg-gray-50 focus:bg-white focus:border-[#166534] outline-none transition-colors"
            />
          </div>

          <div className="ml-auto flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              <span>NSE Live</span>
            </div>
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={clsx(
                "flex items-center gap-1.5 text-sm px-3 py-1.5 rounded border font-medium transition-all",
                chatOpen
                  ? "bg-[#166534] text-white border-[#166534]"
                  : "text-[#166534] border-[#166534] hover:bg-[#f0fdf4]"
              )}
            >
              <Bot className="w-3.5 h-3.5" />
              AI Advisor
            </button>
          </div>
        </div>
      </header>

      {/* ── Index Ticker Bar ── */}
      <div className="bg-[#1e293b] text-white overflow-x-auto">
        <div className="flex min-w-max">
          {INDICES.map((idx, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-5 py-2 border-r border-white/10 shrink-0"
            >
              <span className="text-xs text-slate-400 font-medium">{idx.name}</span>
              <span className="text-sm font-bold">{idx.value}</span>
              <span
                className={clsx(
                  "text-xs font-semibold flex items-center gap-0.5",
                  idx.up ? "text-emerald-400" : "text-red-400"
                )}
              >
                {idx.up ? (
                  <ArrowUpRight className="w-3 h-3" />
                ) : (
                  <ArrowDownRight className="w-3 h-3" />
                )}
                {idx.pct}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="max-w-[1600px] mx-auto px-4 py-4 flex gap-4 items-start">

        {/* ── Left Sidebar ── */}
        <aside className="w-56 shrink-0 space-y-2.5">

          {/* Market */}
          <div className={SIDEBAR_SECTION}>
            <div className={SIDEBAR_HEADER}>
              <span className="flex items-center gap-1.5"><Filter className="w-3 h-3 inline" /> Market</span>
            </div>
            <div className="p-1.5 space-y-0.5">
              {MARKETS.map((m) => (
                <button
                  key={m.label}
                  onClick={() => { set("index", m.index); set("country", m.country); }}
                  className={clsx(
                    SIDEBAR_ITEM,
                    form.index === m.index
                      ? "bg-[#f0fdf4] text-[#166534] font-semibold"
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <span>{m.flag}</span>
                  <span className="text-xs">{m.label}</span>
                  {form.index === m.index && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#166534]" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Investment */}
          <div className={SIDEBAR_SECTION}>
            <div className={SIDEBAR_HEADER}>Investment</div>
            <div className="p-3 space-y-2">
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                  {currency}
                </span>
                <input
                  type="number"
                  value={form.investmentAmount}
                  onChange={(e) => set("investmentAmount", Number(e.target.value))}
                  className="w-full pl-6 pr-2 py-1.5 text-sm border border-gray-300 rounded focus:border-[#166534] outline-none"
                />
              </div>
              <div className="grid grid-cols-3 gap-1">
                {quickAmounts.map(({ v, label }) => (
                  <button
                    key={v}
                    onClick={() => set("investmentAmount", v)}
                    className="text-xs py-1 rounded border border-gray-200 hover:border-[#166534] hover:text-[#166534] text-gray-500 transition-colors"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Risk */}
          <div className={SIDEBAR_SECTION}>
            <div className={SIDEBAR_HEADER}>Risk Profile</div>
            <div className="p-1.5 space-y-0.5">
              {RISK_PROFILES.map((r) => (
                <button
                  key={r.key}
                  onClick={() => set("riskProfile", r.key)}
                  className={clsx(
                    SIDEBAR_ITEM,
                    form.riskProfile === r.key
                      ? "bg-[#f0fdf4] text-[#166534] font-semibold"
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <span className={clsx("w-2 h-2 rounded-full shrink-0", r.dot)} />
                  <span className="text-xs">{r.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Horizon */}
          <div className={SIDEBAR_SECTION}>
            <div className={SIDEBAR_HEADER}>Time Horizon</div>
            <div className="p-1.5 space-y-0.5">
              {HORIZONS.map((h) => (
                <button
                  key={h.key}
                  onClick={() => set("timeHorizon", h.key)}
                  className={clsx(
                    SIDEBAR_ITEM,
                    form.timeHorizon === h.key
                      ? "bg-[#f0fdf4] text-[#166534] font-semibold"
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <span className="text-xs flex-1">{h.label}</span>
                  <span className="text-[10px] text-gray-400">{h.sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Strategy */}
          <div className={SIDEBAR_SECTION}>
            <div className={SIDEBAR_HEADER}>Strategy</div>
            <div className="p-1.5 space-y-0.5">
              {STRATEGIES.map((s) => (
                <button
                  key={s.key}
                  onClick={() => set("strategy", s.key)}
                  className={clsx(
                    SIDEBAR_ITEM,
                    form.strategy === s.key
                      ? "bg-[#f0fdf4] text-[#166534] font-semibold"
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  <span className="text-xs">{s.label}</span>
                  {form.strategy === s.key && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[#166534]" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
            className="w-full bg-[#166534] hover:bg-[#15803d] active:bg-[#14532d] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded flex items-center justify-center gap-2 transition-colors text-sm shadow-sm"
          >
            {analyzeMutation.isPending ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Screening…</>
            ) : (
              <><Zap className="w-3.5 h-3.5" /> Run Screen</>
            )}
          </button>

          {/* Error box */}
          {errorMsg && (
            <div className="rounded border border-red-200 bg-red-50 p-3 space-y-2">
              {errorMsg === "backend_down" ? (
                <>
                  <div className="flex items-center gap-1.5 text-red-600 text-xs font-semibold">
                    <WifiOff className="w-3.5 h-3.5" /> Backend offline
                  </div>
                  <p className="text-[11px] text-gray-500">Run in terminal:</p>
                  <div className="bg-gray-900 rounded p-2 font-mono text-[11px] text-emerald-400">
                    docker compose up -d
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-1.5 text-red-600 text-xs">
                  <AlertCircle className="w-3.5 h-3.5" /> {errorMsg}
                </div>
              )}
            </div>
          )}
        </aside>

        {/* ── Main Content ── */}
        <main className="flex-1 min-w-0 space-y-3">

          {/* Breadcrumb */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div>
              <span className="text-[#166534] font-medium hover:underline cursor-pointer">Screener</span>
              <span className="mx-1.5 text-gray-300">/</span>
              <span className="text-gray-600">{selectedMarket?.label ?? "Custom"}</span>
              <span className="mx-1.5 text-gray-300">/</span>
              <span>{form.strategy} · {RISK_PROFILES.find(r => r.key === form.riskProfile)?.label}</span>
            </div>
            {signals.length > 0 && (
              <span className="text-gray-400">{signals.length} companies found</span>
            )}
          </div>

          {/* Results panel */}
          {(analysisResult || signals.length > 0) && (
            <div className="bg-white rounded border border-gray-200 overflow-hidden shadow-sm">
              {/* Tab bar */}
              <div className="flex items-center border-b border-gray-200 px-4 bg-gray-50">
                {[
                  { key: "signals",  label: `Signals${signals.length ? ` (${signals.length})` : ""}`, show: signals.length > 0 },
                  { key: "analysis", label: "AI Report", show: !!analysisResult },
                ]
                  .filter((t) => t.show)
                  .map((t) => (
                    <button
                      key={t.key}
                      onClick={() => setActiveTab(t.key as any)}
                      className={clsx(
                        "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                        activeTab === t.key
                          ? "border-[#166534] text-[#166534]"
                          : "border-transparent text-gray-500 hover:text-gray-700"
                      )}
                    >
                      {t.label}
                    </button>
                  ))}
                {analysisResult && (
                  <button
                    onClick={() => analyzeMutation.mutate()}
                    className="ml-auto flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors py-2"
                  >
                    <RefreshCw className="w-3 h-3" /> Refresh
                  </button>
                )}
              </div>

              {/* Signals Table */}
              {activeTab === "signals" && signals.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-b border-gray-200">
                        {[
                          ["S.No", "text-left w-10"],
                          ["Company", "text-left"],
                          [`CMP ${currency}`, "text-right"],
                          ["Signal", "text-center"],
                          [`Target ${currency}`, "text-right"],
                          [`Stop Loss ${currency}`, "text-right"],
                          ["Return %", "text-right"],
                          ["RSI", "text-right"],
                          ["Score", "text-right"],
                        ].map(([h, cls]) => (
                          <th
                            key={h}
                            className={clsx("px-4 py-2.5 text-[11px] font-semibold text-gray-500 uppercase tracking-wide", cls)}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map((s: any, i) => {
                        const cfg = ACTION_CFG[s.action] ?? ACTION_CFG.HOLD;
                        const returnPct = s.target_price
                          ? ((s.target_price - s.current_price) / s.current_price) * 100
                          : null;
                        const strengthPct = Math.min(
                          Math.abs(s.score ?? 0) / 6 * 100,
                          100
                        );
                        return (
                          <tr
                            key={s.symbol}
                            className="stock-row border-b border-gray-100 transition-colors cursor-pointer"
                          >
                            <td className="px-4 py-3 text-gray-400 text-xs">{i + 1}</td>
                            <td className="px-4 py-3">
                              <div className="font-semibold text-[#166534] text-sm">{s.symbol}</div>
                              <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1.5">
                                <span>{s.trend?.replace(/_/g, " ")}</span>
                                {s.volume_confirmed && (
                                  <span className="px-1 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 border border-blue-200 font-medium">
                                    Vol ✓
                                  </span>
                                )}
                                {s.macd_crossover && (
                                  <span
                                    className={clsx(
                                      "px-1 py-0.5 rounded text-[10px] font-medium border",
                                      s.macd_crossover === "BULLISH"
                                        ? "bg-emerald-50 text-emerald-600 border-emerald-200"
                                        : "bg-red-50 text-red-600 border-red-200"
                                    )}
                                  >
                                    MACD
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right font-medium text-gray-800">
                              {currency}{Number(s.current_price).toLocaleString("en-IN")}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span
                                className={clsx(
                                  "text-[11px] px-2 py-0.5 rounded border font-semibold whitespace-nowrap",
                                  cfg.color, cfg.bg, cfg.border
                                )}
                              >
                                {cfg.label}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right text-emerald-600 font-medium text-sm">
                              {s.target_price
                                ? `${currency}${Number(s.target_price).toLocaleString("en-IN")}`
                                : "—"}
                            </td>
                            <td className="px-4 py-3 text-right text-red-500 text-sm">
                              {s.stop_loss
                                ? `${currency}${Number(s.stop_loss).toLocaleString("en-IN")}`
                                : "—"}
                            </td>
                            <td
                              className={clsx(
                                "px-4 py-3 text-right font-semibold text-sm",
                                returnPct == null
                                  ? "text-gray-400"
                                  : returnPct >= 0
                                  ? "text-emerald-600"
                                  : "text-red-600"
                              )}
                            >
                              {returnPct != null
                                ? `${returnPct > 0 ? "+" : ""}${returnPct.toFixed(1)}%`
                                : "—"}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div
                                className={clsx(
                                  "text-sm font-semibold",
                                  s.rsi < 35
                                    ? "text-emerald-600"
                                    : s.rsi > 70
                                    ? "text-red-600"
                                    : "text-gray-600"
                                )}
                              >
                                {s.rsi?.toFixed(1)}
                              </div>
                              <div className="text-[10px] text-gray-400">
                                {s.rsi < 35 ? "Oversold" : s.rsi > 70 ? "Overbought" : "Neutral"}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <div className="w-14 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={clsx(
                                      "h-full rounded-full",
                                      s.action?.includes("BUY")
                                        ? "bg-emerald-500"
                                        : s.action?.includes("SELL")
                                        ? "bg-red-500"
                                        : "bg-amber-500"
                                    )}
                                    style={{ width: `${strengthPct}%` }}
                                  />
                                </div>
                                <span className="text-xs text-gray-500 w-7 text-right">
                                  {s.score?.toFixed(1)}
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>

                  {/* Table footer */}
                  <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-400">
                    <span>
                      Showing {signals.length} results · {selectedMarket?.label} ·{" "}
                      {RISK_PROFILES.find((r) => r.key === form.riskProfile)?.label} risk ·{" "}
                      {form.strategy} strategy
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      AI-powered · Claude + MCP
                    </span>
                  </div>
                </div>
              )}

              {/* AI Report */}
              {activeTab === "analysis" && analysisResult && (
                <div className="p-5">
                  <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-gray-100">
                    <div className="w-7 h-7 rounded bg-[#166534] flex items-center justify-center">
                      <TrendingUp className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div>
                      <span className="font-semibold text-gray-800 text-sm">AI Analysis Report</span>
                      <p className="text-[11px] text-gray-400 mt-0.5">
                        {selectedMarket?.label} · {new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                      </p>
                    </div>
                  </div>
                  <div className="text-gray-700 text-sm leading-7 whitespace-pre-wrap max-h-[600px] overflow-y-auto">
                    {analysisResult}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {!analysisResult && signals.length === 0 && !analyzeMutation.isPending && !errorMsg && (
            <div className="bg-white rounded border border-gray-200 shadow-sm">
              <div className="flex flex-col items-center justify-center py-20 text-center px-6">
                <div className="w-16 h-16 rounded-full bg-[#f0fdf4] border-2 border-[#bbf7d0] flex items-center justify-center mb-5">
                  <BarChart2 className="w-7 h-7 text-[#166534]" />
                </div>
                <h2 className="font-bold text-gray-800 text-xl">India's AI Stock Screener</h2>
                <p className="text-gray-400 text-sm mt-2 max-w-md leading-relaxed">
                  Select your market index, investment amount, risk profile, and strategy from the left panel.
                  Click <span className="text-[#166534] font-semibold">Run Screen</span> to get Claude AI-powered stock recommendations.
                </p>
                <div className="mt-8 grid grid-cols-4 gap-3 text-xs w-full max-w-lg">
                  {[
                    { icon: "📈", title: "Nifty 50 / 500", sub: "NSE & BSE stocks" },
                    { icon: "🤖", title: "Claude AI",       sub: "Deep analysis"  },
                    { icon: "⚡", title: "Live Signals",    sub: "Buy/Sell/Hold"  },
                    { icon: "🛡️", title: "Risk-Adjusted",  sub: "Your profile"   },
                  ].map((f) => (
                    <div key={f.title} className="bg-gray-50 rounded-lg p-3 border border-gray-100 text-center">
                      <div className="text-xl mb-1">{f.icon}</div>
                      <div className="font-semibold text-gray-700 text-[11px]">{f.title}</div>
                      <div className="text-gray-400 text-[10px] mt-0.5">{f.sub}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sample table skeleton */}
              <div className="border-t border-gray-100 overflow-hidden opacity-30 pointer-events-none">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      {["S.No", "Company", "CMP ₹", "Signal", "Target ₹", "Return %", "RSI", "Score"].map((h) => (
                        <th key={h} className="px-4 py-2 text-left text-gray-500 font-semibold uppercase tracking-wide">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["1", "RELIANCE",   "2,847", "Strong Buy", "3,200", "+12.4%", "42", "5.2"],
                      ["2", "TCS",        "3,912", "Buy",        "4,500", "+15.0%", "55", "4.8"],
                      ["3", "INFY",       "1,543", "Buy",        "1,750", "+13.4%", "48", "4.5"],
                      ["4", "HDFCBANK",   "1,621", "Hold",       "1,700", "+4.9%",  "52", "3.1"],
                    ].map((row) => (
                      <tr key={row[0]} className="border-b border-gray-100">
                        {row.map((cell, j) => (
                          <td key={j} className="px-4 py-2.5 text-gray-600">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Loading state */}
          {analyzeMutation.isPending && (
            <div className="bg-white rounded border border-gray-200 shadow-sm flex flex-col items-center justify-center py-20">
              <div className="relative mb-5">
                <div className="w-14 h-14 rounded-full border-4 border-[#bbf7d0] border-t-[#166534] animate-spin" />
              </div>
              <p className="font-semibold text-gray-700 text-base">Screening {selectedMarket?.label}…</p>
              <p className="text-gray-400 text-sm mt-1">Claude AI is analyzing stocks for your profile</p>
              <div className="mt-6 space-y-2.5 w-72">
                {[
                  "Fetching NSE/BSE price data",
                  "Running technical analysis",
                  "Scoring & ranking stocks",
                  "Generating recommendations",
                ].map((step, i) => (
                  <div key={step} className="flex items-center gap-3 text-xs text-gray-500">
                    <Loader2
                      className="w-3 h-3 animate-spin text-[#166534] shrink-0"
                      style={{ animationDelay: `${i * 0.25}s` }}
                    />
                    <span>{step}…</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>

        {/* ── AI Chat Panel ── */}
        {chatOpen && (
          <aside className="w-80 shrink-0 h-[calc(100vh-100px)] sticky top-[88px]">
            <AiChat userId={userId} />
          </aside>
        )}
      </div>
    </div>
  );
}
