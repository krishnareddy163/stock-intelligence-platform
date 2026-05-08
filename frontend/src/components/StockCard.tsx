"use client";
import React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { clsx } from "clsx";

interface Signal {
  symbol: string;
  action: string;
  score: number;
  current_price: number;
  target_price: number;
  stop_loss: number;
  rsi: number;
  trend: string;
  reasons: string[];
  strength?: number;
  macd_crossover?: string;
  volume_confirmed?: boolean;
}

interface Props {
  signal: Signal;
  onClick?: () => void;
}

const actionConfig: Record<string, {
  label: string;
  color: string;
  dimColor: string;
  border: string;
  bar: string;
  icon: React.ReactElement;
}> = {
  STRONG_BUY:  { label: "Strong Buy",  color: "text-emerald-400", dimColor: "text-emerald-500/60", border: "border-l-emerald-500", bar: "bg-emerald-500", icon: <TrendingUp  className="w-3.5 h-3.5" /> },
  BUY:         { label: "Buy",         color: "text-green-400",   dimColor: "text-green-500/60",   border: "border-l-green-500",   bar: "bg-green-500",   icon: <TrendingUp  className="w-3.5 h-3.5" /> },
  HOLD:        { label: "Hold",        color: "text-amber-400",   dimColor: "text-amber-500/60",   border: "border-l-amber-500",   bar: "bg-amber-500",   icon: <Minus       className="w-3.5 h-3.5" /> },
  SELL:        { label: "Sell",        color: "text-red-400",     dimColor: "text-red-500/60",     border: "border-l-red-500",     bar: "bg-red-500",     icon: <TrendingDown className="w-3.5 h-3.5" /> },
  STRONG_SELL: { label: "Strong Sell", color: "text-rose-400",    dimColor: "text-rose-500/60",    border: "border-l-rose-500",    bar: "bg-rose-500",    icon: <TrendingDown className="w-3.5 h-3.5" /> },
};

function rsiColor(rsi: number) {
  if (rsi < 35) return "text-emerald-400";
  if (rsi > 70) return "text-rose-400";
  return "text-slate-300";
}

function rsiLabel(rsi: number) {
  if (rsi < 35) return "Oversold";
  if (rsi > 70) return "Overbought";
  return "Neutral";
}

export default function StockCard({ signal, onClick }: Props) {
  const cfg = actionConfig[signal.action] ?? actionConfig.HOLD;

  const returnPct = signal.target_price
    ? ((signal.target_price - signal.current_price) / signal.current_price) * 100
    : null;

  const strengthPct = signal.strength != null
    ? Math.round(signal.strength * 100)
    : Math.min(Math.abs(signal.score) / 6 * 100, 100);

  const isBullish = signal.action.includes("BUY");
  const isBearish = signal.action.includes("SELL");

  return (
    <div
      onClick={onClick}
      className={clsx(
        "group bg-[#0d1117] rounded-2xl border border-white/5 border-l-2 p-4 cursor-pointer",
        "transition-all hover:-translate-y-0.5 hover:border-white/10 hover:shadow-lg hover:shadow-black/30",
        cfg.border
      )}
    >
      {/* Top row */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-white font-bold text-base tracking-tight">{signal.symbol}</span>
            {signal.volume_confirmed && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                Vol ✓
              </span>
            )}
          </div>
          <span className="text-xs text-slate-500 mt-0.5 block">
            {signal.trend?.replace("_", " ")}
            {signal.macd_crossover && (
              <span className={clsx("ml-2", signal.macd_crossover === "BULLISH" ? "text-emerald-500/70" : "text-rose-500/70")}>
                · MACD {signal.macd_crossover.toLowerCase()}
              </span>
            )}
          </span>
        </div>
        <div className={clsx("flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-xl border", cfg.color,
          isBullish ? "bg-emerald-500/10 border-emerald-500/20"
          : isBearish ? "bg-rose-500/10 border-rose-500/20"
          : "bg-amber-500/10 border-amber-500/20"
        )}>
          {cfg.icon}
          {cfg.label}
        </div>
      </div>

      {/* Signal strength bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-slate-600 uppercase tracking-wider">Signal Strength</span>
          <span className={clsx("text-[10px] font-semibold", cfg.dimColor)}>{strengthPct}%</span>
        </div>
        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className={clsx("h-full rounded-full transition-all", cfg.bar)}
            style={{ width: `${strengthPct}%`, opacity: 0.7 }}
          />
        </div>
      </div>

      {/* Price grid */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <PriceStat label="Price" value={`$${signal.current_price?.toFixed(2)}`} />
        <PriceStat
          label="Target"
          value={signal.target_price ? `$${signal.target_price.toFixed(2)}` : "—"}
          color="text-emerald-400"
          sub={returnPct != null ? `${returnPct > 0 ? "+" : ""}${returnPct.toFixed(1)}%` : undefined}
          subColor={returnPct != null && returnPct > 0 ? "text-emerald-500/70" : "text-rose-500/70"}
        />
        <PriceStat
          label="Stop Loss"
          value={signal.stop_loss ? `$${signal.stop_loss.toFixed(2)}` : "—"}
          color="text-rose-400"
        />
      </div>

      {/* RSI */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] text-slate-600 uppercase tracking-wider">RSI ({signal.rsi?.toFixed(1)})</span>
        <span className={clsx("text-xs font-medium", rsiColor(signal.rsi))}>{rsiLabel(signal.rsi)}</span>
      </div>
      <div className="h-1 bg-white/5 rounded-full overflow-hidden mb-3">
        <div
          className={clsx("h-full rounded-full", rsiColor(signal.rsi).replace("text-", "bg-"))}
          style={{ width: `${Math.min(signal.rsi, 100)}%`, opacity: 0.6 }}
        />
      </div>

      {/* Reasons */}
      {signal.reasons?.length > 0 && (
        <div className="border-t border-white/5 pt-3 space-y-1.5">
          {signal.reasons.slice(0, 2).map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-slate-500 group-hover:text-slate-400 transition-colors">
              <span className={clsx("mt-0.5 shrink-0", cfg.dimColor)}>›</span>
              <span className="leading-relaxed">{r}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PriceStat({
  label, value, color = "text-slate-300", sub, subColor,
}: {
  label: string; value: string; color?: string; sub?: string; subColor?: string;
}) {
  return (
    <div>
      <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-1">{label}</p>
      <p className={clsx("text-sm font-semibold", color)}>{value}</p>
      {sub && <p className={clsx("text-[10px] font-medium mt-0.5", subColor)}>{sub}</p>}
    </div>
  );
}
