import { test, expect } from "@playwright/test";

test.describe("AI Chat Panel", () => {

  test.beforeEach(async ({ page }) => {
    // Mock the AI orchestrator /chat endpoint
    await page.route("**/chat", route =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_id: "demo-user",
          response: "TCS is trading at ₹3912. Strong fundamentals, IT sector leader. Recommend BUY.",
          latency_ms: 950,
          tool_calls_count: 0,
        }),
      })
    );

    await page.goto("/");
    // Open the chat panel
    await page.getByRole("button", { name: /ai advisor/i }).click();
    await page.getByText("AI Stock Advisor").waitFor();
  });

  // ── Initial state ───────────────────────────────────────────────

  test("shows initial greeting from assistant", async ({ page }) => {
    await expect(page.getByText(/Namaste/i)).toBeVisible();
  });

  test("shows suggestion chips", async ({ page }) => {
    await expect(page.getByText("Best Nifty 50 stocks for 2025?")).toBeVisible();
    await expect(page.getByText("Build a ₹1L growth portfolio")).toBeVisible();
  });

  test("shows Claude + MCP badge in header", async ({ page }) => {
    await expect(page.getByText(/Claude \+ MCP/i)).toBeVisible();
  });

  // ── Sending messages ────────────────────────────────────────────

  test("user can type and send a message", async ({ page }) => {
    const input = page.getByPlaceholder(/ask about/i);
    await input.fill("Is TCS a good buy?");
    await page.keyboard.press("Enter");

    await expect(page.getByText("Is TCS a good buy?")).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText(/TCS is trading at ₹3912/)).toBeVisible({ timeout: 8_000 });
  });

  test("clicking suggestion chip sends the suggestion as a message", async ({ page }) => {
    await page.route("**/chat", route =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ response: "Here are the top Nifty 50 picks for 2025..." }),
      })
    );

    await page.getByText("Best Nifty 50 stocks for 2025?").click();

    await expect(
      page.getByText("Best Nifty 50 stocks for 2025?").last()
    ).toBeVisible({ timeout: 8_000 });
  });

  test("input clears after sending a message", async ({ page }) => {
    const input = page.getByPlaceholder(/ask about/i);
    await input.fill("Test message");
    await page.keyboard.press("Enter");

    await expect(input).toHaveValue("", { timeout: 5_000 });
  });

  test("send button is present and clickable", async ({ page }) => {
    const input = page.getByPlaceholder(/ask about/i);
    await input.fill("Another question");
    const sendBtn = page.getByRole("button", { name: /send/i });
    await sendBtn.click();

    await expect(page.getByText("Another question")).toBeVisible({ timeout: 8_000 });
  });

  // ── Error handling ──────────────────────────────────────────────

  test("shows error message when orchestrator is offline", async ({ page }) => {
    await page.route("**/chat", route => route.abort("failed"));

    const input = page.getByPlaceholder(/ask about/i);
    await input.fill("Will this fail?");
    await page.keyboard.press("Enter");

    await expect(
      page.getByText(/orchestrator isn't running/i)
    ).toBeVisible({ timeout: 8_000 });
  });

  // ── Conversation continuity ─────────────────────────────────────

  test("multiple messages appear in sequence", async ({ page }) => {
    const input = page.getByPlaceholder(/ask about/i);

    await input.fill("Question one");
    await page.keyboard.press("Enter");
    await page.getByText(/TCS is trading/).waitFor({ timeout: 8_000 });

    // Mock second response
    await page.route("**/chat", route =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ response: "Infosys also looks attractive at current levels." }),
      })
    );

    await input.fill("What about Infosys?");
    await page.keyboard.press("Enter");

    await expect(page.getByText("What about Infosys?")).toBeVisible({ timeout: 8_000 });
    await expect(page.getByText(/Infosys also looks/)).toBeVisible({ timeout: 8_000 });
  });

  // ── Mobile layout ───────────────────────────────────────────────

  test("chat input is visible on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByPlaceholder(/ask about/i)).toBeVisible();
  });
});
