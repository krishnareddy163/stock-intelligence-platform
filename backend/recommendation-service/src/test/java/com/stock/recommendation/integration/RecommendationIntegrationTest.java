package com.stock.recommendation.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.recommendation.client.McpClient;
import com.stock.recommendation.dto.RecommendationRequest;
import org.junit.jupiter.api.*;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.MediaType;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class RecommendationIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper objectMapper;

    @MockBean McpClient mcpClient;
    @MockBean RedisTemplate<String, Object> redisTemplate;
    @MockBean KafkaTemplate<String, Object> kafkaTemplate;

    private static final String USER_ID = UUID.randomUUID().toString();

    @BeforeEach
    void setupMocks() {
        // Redis cache always misses so service calls through to MCP
        var ops = Mockito.mock(org.springframework.data.redis.core.ValueOperations.class);
        Mockito.when(redisTemplate.opsForValue()).thenReturn(ops);
        Mockito.when(ops.get(anyString())).thenReturn(null);

        // MCP returns a minimal analysis string
        Mockito.when(mcpClient.callOrchestrator(any()))
               .thenReturn(Map.of("analysis", "RELIANCE is a strong buy. Target: ₹3200.",
                                  "tool_calls", List.of()));

        // Kafka fire-and-forget: ignore failures
        Mockito.when(kafkaTemplate.send(anyString(), any()))
               .thenReturn(null);
    }

    // ── Analyze ───────────────────────────────────────────────────

    @Test @Order(1)
    void analyze_validRequest_returns200WithAnalysis() throws Exception {
        var req = buildRequest(USER_ID, "NIFTY50", 100000.0, "MEDIUM");

        mvc.perform(post("/api/v1/recommendations/analyze")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.analysis").isNotEmpty())
           .andExpect(jsonPath("$.userId").value(USER_ID));
    }

    @Test @Order(2)
    void analyze_missingUserId_returns422() throws Exception {
        var req = buildRequest(null, "NIFTY50", 50000.0, "LOW");

        mvc.perform(post("/api/v1/recommendations/analyze")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isUnprocessableEntity());
    }

    @Test @Order(3)
    void analyze_negativeAmount_returns422() throws Exception {
        var req = buildRequest(USER_ID, "NIFTY50", -1000.0, "LOW");

        mvc.perform(post("/api/v1/recommendations/analyze")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isUnprocessableEntity());
    }

    // ── History ───────────────────────────────────────────────────

    @Test @Order(4)
    void getHistory_defaultLimit_returnsEmptyListForNewUser() throws Exception {
        mvc.perform(get("/api/v1/recommendations/history/{userId}", UUID.randomUUID()))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$").isArray());
    }

    @Test @Order(5)
    void getHistory_customLimit_respectsLimit() throws Exception {
        mvc.perform(get("/api/v1/recommendations/history/{userId}", USER_ID)
                .param("limit", "5"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$").isArray());
    }

    // ── Quick Scan ────────────────────────────────────────────────

    @Test @Order(6)
    void quickScan_validSymbols_returns200() throws Exception {
        Mockito.when(mcpClient.callOrchestrator(any()))
               .thenReturn(Map.of("signals", List.of(
                   Map.of("symbol", "RELIANCE", "action", "BUY", "score", 8)
               )));

        mvc.perform(post("/api/v1/recommendations/quick-scan")
                .param("symbols", "RELIANCE.NS,TCS.NS")
                .param("riskProfile", "MEDIUM"))
           .andExpect(status().isOk());
    }

    // ── Health ────────────────────────────────────────────────────

    @Test @Order(7)
    void health_returnsHealthy() throws Exception {
        mvc.perform(get("/api/v1/recommendations/health"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.status").value("healthy"));
    }

    // ── Helpers ───────────────────────────────────────────────────

    private RecommendationRequest buildRequest(String userId, String index,
                                               double amount, String risk) {
        var req = new RecommendationRequest();
        if (userId != null) req.setUserId(UUID.fromString(userId));
        req.setQuery("Best stocks for " + index);
        req.setIndex(index);
        req.setCountry("IN");
        req.setInvestmentAmount(new BigDecimal(amount));
        req.setRiskProfile(risk);
        req.setTimeHorizon("LONG_TERM");
        req.setStrategy("GROWTH");
        req.setPreferredSectors(List.of());
        return req;
    }
}
