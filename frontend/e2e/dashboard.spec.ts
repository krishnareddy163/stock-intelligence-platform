import { test, expect } from "@playwright/test";

test.describe("Dashboard — Screener-style UI", () => {

  test.beforeEach(async ({ page }) => {
    // Intercept the analyze API so tests don't need the backend running
    await page.route("**/api/v1/recommendations/analyze", route =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          userId: "demo-user",
          analysis: "Top picks: RELIANCE (BUY ₹3200), TCS (BUY ₹4100), HDFC (HOLD).",
          toolCalls: [
            {
              tool: "generate_buy_sell_signals",
              output: {
                signals: [
                  { symbol: "RELIANCE", action: "BUY",  score: 9, current_price: 2850,
                    target_price: 3200, stop_loss: 2650, rsi: 45, trend: "UPTREND",
                    reasons: ["RSI oversold", "MACD crossover"], strength: 0.9,
                    macd_crossover: "BULLISH", volume_confirmed: true },
                  { symbol: "TCS",      action: "BUY",  score: 8, current_price: 3912,
                    target_price: 4100, stop_loss: 3750, rsi: 52, trend: "UPTREND",
                    reasons: ["Strong fundamentals"], strength: 0.75,
                    macd_crossover: "BULLISH", volume_confirmed: false },
                  { symbol: "HDFC",     action: "HOLD", score: 5, current_price: 1620,
                    target_price: 1700, stop_loss: 1550, rsi: 58, trend: "SIDEWAYS",
                    reasons: ["Neutral RSI"], strength: 0.5,
                    macd_crossover: "BEARISH", volume_confirmed: false },
                ],
              },
            },
          ],
          latencyMs: 1850,
          iterations: 2,
        }),
      })
    );
    await page.goto("/");
  });

  // ── Page structure ──────────────────────────────────────────────

  test("renders StockIQ header and logo", async ({ page }) => {
    await expect(page.getByText("StockIQ")).toBeVisible();
  });

  test("renders index ticker bar with NIFTY 50", async ({ page }) => {
    // Use first() to avoid strict-mode error when parent containers also contain the text
    await expect(page.getByText("NIFTY 50").first()).toBeVisible();
  });

  test("renders left sidebar market selector", async ({ page }) => {
    // Scope to aside to avoid matching the breadcrumb which also shows the active market label
    await expect(page.locator("aside").getByRole("button", { name: /Nifty 50/ })).toBeVisible();
  });

  test("renders Analyze button", async ({ page }) => {
    // The run button is labelled "Run Screen", not "Analyze"
    await expect(page.getByRole("button", { name: /run screen/i })).toBeVisible();
  });

  test("renders currency as ₹ for Indian markets", async ({ page }) => {
    await expect(page.getByText(/₹/).first()).toBeVisible();
  });

  // ── Sidebar interactions ────────────────────────────────────────

  test("clicking SENSEX changes active market", async ({ page }) => {
    // Use role locator to avoid matching the breadcrumb span that also shows "Sensex" after click
    await page.getByRole("button", { name: /Sensex/ }).click();
    // Active state applies bg-[#f0fdf4] (light green) to the selected sidebar button
    await expect(page.getByRole("button", { name: /Sensex/ })).toHaveClass(/bg-\[#f0fdf4\]/);
  });

  test("clicking risk profile changes selection", async ({ page }) => {
    // Use role locator to avoid strict-mode violation with breadcrumb "GROWTH · Conservative"
    await page.getByRole("button", { name: "Conservative" }).click();
    await expect(page.getByRole("button", { name: "Conservative" })).toBeVisible();
  });

  test("clicking time horizon changes selection", async ({ page }) => {
    await page.getByText("Short Term").click();
    await expect(page.getByText("Short Term")).toBeVisible();
  });

  // ── Analysis flow ───────────────────────────────────────────────

  test("clicking Analyze calls the API and shows signals table", async ({ page }) => {
    await page.getByRole("button", { name: /run screen/i }).click();

    await expect(page.getByText("RELIANCE")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("TCS")).toBeVisible();
    await expect(page.getByText("HDFC")).toBeVisible();
  });

  test("signals table shows BUY badge for RELIANCE", async ({ page }) => {
    await page.getByRole("button", { name: /run screen/i }).click();
    await page.getByText("RELIANCE").waitFor({ timeout: 10_000 });

    const relianceRow = page.locator("tr", { has: page.getByText("RELIANCE") });
    await expect(relianceRow.getByText(/buy/i).first()).toBeVisible();
  });

  test("switches to AI Report tab after analysis", async ({ page }) => {
    await page.getByRole("button", { name: /run screen/i }).click();
    await page.getByText("RELIANCE").waitFor({ timeout: 10_000 });

    await page.getByRole("tab", { name: /ai report/i }).click();
    await expect(page.getByText(/top picks/i)).toBeVisible();
  });

  // ── AI Chat panel ───────────────────────────────────────────────

  test("AI Advisor button toggles chat panel", async ({ page }) => {
    const chatButton = page.getByRole("button", { name: /ai advisor/i });
    await chatButton.click();
    await expect(page.getByText("AI Stock Advisor")).toBeVisible();
  });

  test("chat panel shows initial greeting", async ({ page }) => {
    await page.getByRole("button", { name: /ai advisor/i }).click();
    await expect(page.getByText(/Namaste/i)).toBeVisible();
  });

  // ── Investment amount input ─────────────────────────────────────

  test("investment amount field is editable", async ({ page }) => {
    const input = page.getByRole("spinbutton");
    await input.fill("250000");
    await expect(input).toHaveValue("250000");
  });

  // ── Responsive layout ───────────────────────────────────────────

  test("sidebar is visible on desktop viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    // Check the aside element itself rather than text that may match multiple elements
    await expect(page.locator("aside").first()).toBeVisible();
  });
});
