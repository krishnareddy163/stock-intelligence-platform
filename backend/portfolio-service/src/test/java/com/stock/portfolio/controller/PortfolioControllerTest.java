package com.stock.portfolio.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.portfolio.dto.CreatePortfolioRequest;
import com.stock.portfolio.entity.Portfolio;
import com.stock.portfolio.service.PortfolioService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(PortfolioController.class)
class PortfolioControllerTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private ObjectMapper objectMapper;
    @MockBean  private PortfolioService portfolioService;

    private Portfolio portfolio;
    private UUID portfolioId;
    private UUID userId;

    @BeforeEach
    void setUp() {
        userId = UUID.randomUUID();
        portfolioId = UUID.randomUUID();

        portfolio = Portfolio.builder()
                .portfolioId(portfolioId)
                .userId(userId)
                .portfolioName("Test Portfolio")
                .totalInvestment(BigDecimal.valueOf(100000))
                .initialInvestment(BigDecimal.valueOf(100000))
                .strategy(Portfolio.Strategy.GROWTH)
                .timeHorizon(Portfolio.TimeHorizon.LONG_TERM)
                .riskScore(50)
                .build();
    }

    @Test
    void createPortfolio_validRequest_returns200() throws Exception {
        CreatePortfolioRequest req = new CreatePortfolioRequest();
        req.setUserId(userId.toString());
        req.setPortfolioName("Test Portfolio");
        req.setSymbols(List.of("RELIANCE", "TCS"));
        req.setTotalInvestment(100000.0);
        req.setRiskProfile("MEDIUM");
        req.setStrategy("GROWTH");
        req.setTimeHorizon("LONG_TERM");

        when(portfolioService.createPortfolio(any())).thenReturn(portfolio);

        mockMvc.perform(post("/api/v1/portfolios")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.portfolioId").value(portfolioId.toString()))
                .andExpect(jsonPath("$.portfolioName").value("Test Portfolio"));
    }

    @Test
    void createPortfolio_missingUserId_returns400() throws Exception {
        CreatePortfolioRequest req = new CreatePortfolioRequest();
        req.setTotalInvestment(100000.0);

        mockMvc.perform(post("/api/v1/portfolios")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getUserPortfolios_returnsPortfolioList() throws Exception {
        when(portfolioService.getUserPortfolios(userId.toString())).thenReturn(List.of(portfolio));

        mockMvc.perform(get("/api/v1/portfolios/user/{userId}", userId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].portfolioId").value(portfolioId.toString()));
    }

    @Test
    void getUserPortfolios_noPortfolios_returnsEmptyArray() throws Exception {
        when(portfolioService.getUserPortfolios(anyString())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/portfolios/user/{userId}", userId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$").isEmpty());
    }

    @Test
    void getPortfolio_found_returns200() throws Exception {
        when(portfolioService.getPortfolio(portfolioId.toString())).thenReturn(Optional.of(portfolio));

        mockMvc.perform(get("/api/v1/portfolios/{id}", portfolioId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.portfolioId").value(portfolioId.toString()));
    }

    @Test
    void getPortfolio_notFound_returns404() throws Exception {
        when(portfolioService.getPortfolio(anyString())).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/portfolios/{id}", portfolioId))
                .andExpect(status().isNotFound());
    }

    @Test
    void rebalance_validId_returns200() throws Exception {
        when(portfolioService.rebalancePortfolio(portfolioId.toString())).thenReturn(portfolio);

        mockMvc.perform(post("/api/v1/portfolios/{id}/rebalance", portfolioId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.portfolioId").value(portfolioId.toString()));
    }

    @Test
    void health_returns200() throws Exception {
        mockMvc.perform(get("/api/v1/portfolios/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("healthy"))
                .andExpect(jsonPath("$.service").value("portfolio-service"));
    }
}
