import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { api, orchestratorApi, authApi, recommendationApi, portfolioApi, aiApi } from "@/services/api";

const mockApi = new MockAdapter(api);
const mockOrchestrator = new MockAdapter(orchestratorApi);

afterEach(() => {
  mockApi.reset();
  mockOrchestrator.reset();
  localStorage.clear();
});

// ── Auth ──────────────────────────────────────────────────────────

describe("authApi", () => {
  it("login sends POST to /api/v1/auth/login with credentials", async () => {
    mockApi.onPost("/api/v1/auth/login").reply(200, { token: "jwt-abc", email: "test@test.com" });
    const res = await authApi.login("test@test.com", "password123");
    expect(res.data.token).toBe("jwt-abc");
  });

  it("register sends POST to /api/v1/auth/register", async () => {
    mockApi.onPost("/api/v1/auth/register").reply(201, { email: "new@test.com" });
    const res = await authApi.register({
      name: "Test User",
      email: "new@test.com",
      password: "password123",
      country: "IN",
      riskProfile: "MEDIUM",
    });
    expect(res.status).toBe(201);
  });
});

// ── Recommendations ───────────────────────────────────────────────

describe("recommendationApi", () => {
  it("analyze sends POST to /api/v1/recommendations/analyze", async () => {
    const mockResponse = { analysis: "RELIANCE is a buy", tool_calls: [], latency_ms: 1200 };
    mockApi.onPost("/api/v1/recommendations/analyze").reply(200, mockResponse);

    const res = await recommendationApi.analyze({
      userId: "user-1",
      query: "Best Nifty stocks",
      country: "IN",
      index: "NIFTY50",
      investmentAmount: 100000,
      riskProfile: "MEDIUM",
      timeHorizon: "LONG_TERM",
      strategy: "GROWTH",
      preferredSectors: [],
    });
    expect(res.data.analysis).toBe("RELIANCE is a buy");
  });

  it("quickScan sends POST with symbols as query param", async () => {
    mockApi.onPost("/api/v1/recommendations/quick-scan").reply(200, { signals: [] });
    const res = await recommendationApi.quickScan(["RELIANCE.NS", "TCS.NS"], "HIGH");
    expect(res.status).toBe(200);
  });

  it("getHistory sends GET with userId and limit", async () => {
    mockApi.onGet("/api/v1/recommendations/history/user-1").reply(200, []);
    const res = await recommendationApi.getHistory("user-1", 10);
    expect(res.data).toEqual([]);
  });
});

// ── Portfolios ────────────────────────────────────────────────────

describe("portfolioApi", () => {
  it("create sends POST to /api/v1/portfolios", async () => {
    mockApi.onPost("/api/v1/portfolios").reply(201, { portfolioId: "p-1" });
    const res = await portfolioApi.create({
      userId: "user-1",
      portfolioName: "My Portfolio",
      symbols: ["RELIANCE.NS"],
      totalInvestment: 100000,
      riskProfile: "MEDIUM",
      strategy: "GROWTH",
      timeHorizon: "LONG_TERM",
    });
    expect(res.data.portfolioId).toBe("p-1");
  });

  it("getAll sends GET to /api/v1/portfolios/user/:userId", async () => {
    mockApi.onGet("/api/v1/portfolios/user/user-1").reply(200, [{ portfolioId: "p-1" }]);
    const res = await portfolioApi.getAll("user-1");
    expect(res.data).toHaveLength(1);
  });

  it("rebalance sends POST to /api/v1/portfolios/:id/rebalance", async () => {
    mockApi.onPost("/api/v1/portfolios/p-1/rebalance").reply(200, { portfolioId: "p-1" });
    const res = await portfolioApi.rebalance("p-1");
    expect(res.status).toBe(200);
  });
});

// ── AI Chat ───────────────────────────────────────────────────────

describe("aiApi", () => {
  it("chat sends POST to orchestrator /chat", async () => {
    mockOrchestrator.onPost("/chat").reply(200, { response: "TCS looks bullish." });
    const res = await aiApi.chat("Is TCS good?", "user-1", []);
    expect(res.data.response).toBe("TCS looks bullish.");
  });

  it("healthCheck sends GET to orchestrator /health", async () => {
    mockOrchestrator.onGet("/health").reply(200, { status: "healthy" });
    const res = await aiApi.healthCheck();
    expect(res.data.status).toBe("healthy");
  });
});

// ── Auth interceptor ──────────────────────────────────────────────

describe("request interceptor", () => {
  it("adds Authorization header when token exists in localStorage", async () => {
    localStorage.setItem("token", "my-jwt-token");
    mockApi.onGet("/api/v1/portfolios/user/u1").reply(200, []);

    await portfolioApi.getAll("u1");

    const request = mockApi.history.get[0];
    expect(request.headers?.Authorization).toBe("Bearer my-jwt-token");
  });

  it("does not add Authorization header when no token", async () => {
    mockApi.onGet("/api/v1/portfolios/user/u2").reply(200, []);
    await portfolioApi.getAll("u2");

    const request = mockApi.history.get[0];
    expect(request.headers?.Authorization).toBeUndefined();
  });
});
