import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const ORCHESTRATOR_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || "http://localhost:5000";

export const api = axios.create({ baseURL: BASE_URL, timeout: 90000 });
export const orchestratorApi = axios.create({ baseURL: ORCHESTRATOR_URL, timeout: 90000 });

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Auth ────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/api/v1/auth/login", { email, password }),
  register: (data: RegisterData) =>
    api.post("/api/v1/auth/register", data),
};

// ─── Recommendations ────────────────────────────────────────
export const recommendationApi = {
  analyze: (req: AnalysisRequest) =>
    api.post("/api/v1/recommendations/analyze", req),
  quickScan: (symbols: string[], riskProfile = "MEDIUM") =>
    api.post("/api/v1/recommendations/quick-scan", null, {
      params: { symbols: symbols.join(","), riskProfile },
    }),
  getHistory: (userId: string, limit = 20) =>
    api.get(`/api/v1/recommendations/history/${userId}`, { params: { limit } }),
};

// ─── Portfolios ──────────────────────────────────────────────
export const portfolioApi = {
  create: (req: CreatePortfolioRequest) =>
    api.post("/api/v1/portfolios", req),
  getAll: (userId: string) =>
    api.get(`/api/v1/portfolios/user/${userId}`),
  getById: (id: string) =>
    api.get(`/api/v1/portfolios/${id}`),
  rebalance: (id: string) =>
    api.post(`/api/v1/portfolios/${id}/rebalance`),
};

// ─── AI Chat (direct to orchestrator) ───────────────────────
export const aiApi = {
  chat: (message: string, userId: string, history: ChatMessage[] = []) =>
    orchestratorApi.post("/chat", {
      user_id: userId,
      message,
      conversation_history: history,
    }),
  healthCheck: () => orchestratorApi.get("/health"),
};

// ─── Types ──────────────────────────────────────────────────
export interface RegisterData {
  name: string;
  email: string;
  password: string;
  country: string;
  riskProfile: string;
}

export interface AnalysisRequest {
  userId: string;
  query: string;
  country: string;
  index: string;
  investmentAmount: number;
  riskProfile: string;
  timeHorizon: string;
  strategy: string;
  preferredSectors: string[];
}

export interface CreatePortfolioRequest {
  userId: string;
  portfolioName: string;
  symbols: string[];
  totalInvestment: number;
  riskProfile: string;
  strategy: string;
  timeHorizon: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
