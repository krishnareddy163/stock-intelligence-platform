package com.stock.recommendation.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.recommendation.dto.RecommendationRequest;
import com.stock.recommendation.entity.Recommendation;
import com.stock.recommendation.service.RecommendationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(RecommendationController.class)
class RecommendationControllerTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @MockBean  private RecommendationService recommendationService;

    private RecommendationRequest validRequest;

    @BeforeEach
    void setUp() {
        validRequest = new RecommendationRequest();
        validRequest.setUserId("user-123");
        validRequest.setCountry("IN");
        validRequest.setIndex("NIFTY50");
        validRequest.setInvestmentAmount(100000.0);
        validRequest.setRiskProfile("MEDIUM");
        validRequest.setTimeHorizon("LONG_TERM");
        validRequest.setStrategy("GROWTH");
        validRequest.setPreferredSectors(List.of());
        validRequest.setQuery("Best Nifty stocks");
    }

    @Test
    void analyze_validRequest_returns200() throws Exception {
        Map<String, Object> response = Map.of(
                "userId", "user-123",
                "index", "NIFTY50",
                "analysis", "Buy RELIANCE and TCS",
                "latencyMs", 1500L,
                "generatedAt", LocalDateTime.now().toString()
        );
        when(recommendationService.generateRecommendations(any())).thenReturn(response);

        mockMvc.perform(post("/api/v1/recommendations/analyze")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value("user-123"))
                .andExpect(jsonPath("$.index").value("NIFTY50"))
                .andExpect(jsonPath("$.analysis").value("Buy RELIANCE and TCS"));
    }

    @Test
    void analyze_missingUserId_returns400() throws Exception {
        RecommendationRequest invalid = new RecommendationRequest();
        invalid.setCountry("IN");
        invalid.setIndex("NIFTY50");
        invalid.setInvestmentAmount(100000.0);

        mockMvc.perform(post("/api/v1/recommendations/analyze")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalid)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void analyze_missingCountry_returns400() throws Exception {
        RecommendationRequest invalid = new RecommendationRequest();
        invalid.setUserId("user-123");
        invalid.setIndex("NIFTY50");
        invalid.setInvestmentAmount(100000.0);

        mockMvc.perform(post("/api/v1/recommendations/analyze")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalid)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void analyze_negativeAmount_returns400() throws Exception {
        validRequest.setInvestmentAmount(-1000.0);

        mockMvc.perform(post("/api/v1/recommendations/analyze")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(validRequest)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getHistory_validUserId_returnsList() throws Exception {
        UUID uid = UUID.randomUUID();
        Recommendation rec = Recommendation.builder()
                .userId(uid)
                .stockSymbol("RELIANCE")
                .recommendationType(Recommendation.RecommendationType.BUY)
                .generatedAt(LocalDateTime.now())
                .build();

        when(recommendationService.getUserHistory(anyString(), anyInt())).thenReturn(List.of(rec));

        mockMvc.perform(get("/api/v1/recommendations/history/{userId}", uid)
                        .param("limit", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$[0].stockSymbol").value("RELIANCE"));
    }

    @Test
    void getHistory_defaultLimit_uses20() throws Exception {
        when(recommendationService.getUserHistory(anyString(), eq(20))).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/recommendations/history/{userId}", UUID.randomUUID()))
                .andExpect(status().isOk());
    }

    @Test
    void quickScan_validSymbols_returns200() throws Exception {
        Map<String, Object> scanResult = Map.of(
                "signals", List.of(Map.of("symbol", "RELIANCE", "action", "BUY")),
                "scannedAt", LocalDateTime.now().toString()
        );
        when(recommendationService.quickScan(anyList(), anyString())).thenReturn(scanResult);

        mockMvc.perform(post("/api/v1/recommendations/quick-scan")
                        .param("symbols", "RELIANCE", "TCS")
                        .param("riskProfile", "MEDIUM"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.signals").isArray());
    }

    @Test
    void quickScan_defaultRiskProfile_usesMedium() throws Exception {
        when(recommendationService.quickScan(anyList(), eq("MEDIUM"))).thenReturn(Map.of("signals", List.of()));

        mockMvc.perform(post("/api/v1/recommendations/quick-scan")
                        .param("symbols", "RELIANCE"))
                .andExpect(status().isOk());
    }

    @Test
    void health_returns200() throws Exception {
        mockMvc.perform(get("/api/v1/recommendations/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.service").value("recommendation-service"));
    }
}
