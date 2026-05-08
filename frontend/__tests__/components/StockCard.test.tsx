import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StockCard from "@/components/StockCard";

const baseSignal = {
  symbol: "RELIANCE",
  action: "BUY",
  score: 8,
  current_price: 2850.75,
  target_price: 3200.0,
  stop_loss: 2650.0,
  rsi: 45.2,
  trend: "UPTREND",
  reasons: ["RSI in healthy zone", "MACD bullish crossover"],
  strength: 0.8,
  macd_crossover: "BULLISH",
  volume_confirmed: true,
};

describe("StockCard", () => {
  it("renders stock symbol", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("RELIANCE")).toBeInTheDocument();
  });

  it("renders BUY action badge", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("Buy")).toBeInTheDocument();
  });

  it("renders STRONG_BUY action badge", () => {
    render(<StockCard signal={{ ...baseSignal, action: "STRONG_BUY" }} />);
    expect(screen.getByText("Strong Buy")).toBeInTheDocument();
  });

  it("renders SELL action badge", () => {
    render(<StockCard signal={{ ...baseSignal, action: "SELL" }} />);
    expect(screen.getByText("Sell")).toBeInTheDocument();
  });

  it("renders HOLD action badge", () => {
    render(<StockCard signal={{ ...baseSignal, action: "HOLD" }} />);
    expect(screen.getByText("Hold")).toBeInTheDocument();
  });

  it("renders current price", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("$2850.75")).toBeInTheDocument();
  });

  it("renders target price", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("$3200.00")).toBeInTheDocument();
  });

  it("renders stop loss price", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("$2650.00")).toBeInTheDocument();
  });

  it("renders volume confirmed badge when volume_confirmed=true", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("Vol ✓")).toBeInTheDocument();
  });

  it("does not render volume badge when volume_confirmed=false", () => {
    render(<StockCard signal={{ ...baseSignal, volume_confirmed: false }} />);
    expect(screen.queryByText("Vol ✓")).not.toBeInTheDocument();
  });

  it("renders MACD crossover label", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText(/macd bullish/i)).toBeInTheDocument();
  });

  it("renders first reason", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText("RSI in healthy zone")).toBeInTheDocument();
  });

  it("shows at most 2 reasons", () => {
    const manyReasons = {
      ...baseSignal,
      reasons: ["Reason 1", "Reason 2", "Reason 3", "Reason 4"],
    };
    render(<StockCard signal={manyReasons} />);
    expect(screen.getByText("Reason 1")).toBeInTheDocument();
    expect(screen.getByText("Reason 2")).toBeInTheDocument();
    expect(screen.queryByText("Reason 3")).not.toBeInTheDocument();
  });

  it("calls onClick when card is clicked", async () => {
    const onClick = jest.fn();
    render(<StockCard signal={baseSignal} onClick={onClick} />);
    await userEvent.click(screen.getByText("RELIANCE").closest("div")!);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("renders signal strength percentage", () => {
    render(<StockCard signal={{ ...baseSignal, strength: 0.75 }} />);
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("handles missing target price gracefully", () => {
    render(<StockCard signal={{ ...baseSignal, target_price: 0 }} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders RSI value", () => {
    render(<StockCard signal={baseSignal} />);
    expect(screen.getByText(/RSI \(45\.2\)/i)).toBeInTheDocument();
  });

  it("shows Oversold for RSI < 35", () => {
    render(<StockCard signal={{ ...baseSignal, rsi: 28.5 }} />);
    expect(screen.getByText("Oversold")).toBeInTheDocument();
  });

  it("shows Overbought for RSI > 70", () => {
    render(<StockCard signal={{ ...baseSignal, rsi: 78.0 }} />);
    expect(screen.getByText("Overbought")).toBeInTheDocument();
  });

  it("shows Neutral for RSI between 35 and 70", () => {
    render(<StockCard signal={{ ...baseSignal, rsi: 52.0 }} />);
    expect(screen.getByText("Neutral")).toBeInTheDocument();
  });
});
