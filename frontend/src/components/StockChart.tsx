"use client";
import { useEffect, useRef } from "react";
import { createChart, ColorType, IChartApi } from "lightweight-charts";

interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface Props {
  data: CandleData[];
  symbol: string;
  height?: number;
}

export default function StockChart({ data, symbol, height = 400 }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return;

    chartInstance.current = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#0f172a" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#1e293b" },
      timeScale: { borderColor: "#1e293b", timeVisible: true },
      width: chartRef.current.clientWidth,
      height,
    });

    const candleSeries = chartInstance.current.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    candleSeries.setData(data);
    chartInstance.current.timeScale().fitContent();

    const handleResize = () => {
      if (chartRef.current && chartInstance.current) {
        chartInstance.current.applyOptions({ width: chartRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance.current?.remove();
    };
  }, [data, height]);

  return (
    <div className="bg-slate-900 rounded-xl p-4 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-semibold text-lg">{symbol}</h3>
        <span className="text-slate-400 text-sm">Price Chart</span>
      </div>
      <div ref={chartRef} />
    </div>
  );
}
