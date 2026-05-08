package com.stock.portfolio.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.portfolio.dto.CreatePortfolioRequest;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class PortfolioIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper objectMapper;
    @MockBean  RestTemplate restTemplate;

    private static final String USER_ID = UUID.randomUUID().toString();
    private static String createdPortfolioId;

    // ── Create ────────────────────────────────────────────────────

    @Test @Order(1)
    void createPortfolio_validRequest_returns201() throws Exception {
        var req = new CreatePortfolioRequest();
        req.setUserId(UUID.fromString(USER_ID));
        req.setPortfolioName("Nifty Growth Portfolio");
        req.setSymbols(List.of("RELIANCE.NS", "TCS.NS", "HDFC.NS"));
        req.setTotalInvestment(new BigDecimal("100000"));
        req.setRiskProfile("MEDIUM");
        req.setStrategy("GROWTH");
        req.setTimeHorizon("LONG_TERM");

        var result = mvc.perform(post("/api/v1/portfolios")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isCreated())
           .andExpect(jsonPath("$.portfolioName").value("Nifty Growth Portfolio"))
           .andExpect(jsonPath("$.portfolioId").isNotEmpty())
           .andReturn();

        var body = objectMapper.readTree(result.getResponse().getContentAsString());
        createdPortfolioId = body.get("portfolioId").asText();
    }

    @Test @Order(2)
    void createPortfolio_missingUserId_returns422() throws Exception {
        var req = new CreatePortfolioRequest();
        req.setPortfolioName("Bad Portfolio");
        req.setSymbols(List.of("TCS.NS"));
        req.setTotalInvestment(new BigDecimal("50000"));

        mvc.perform(post("/api/v1/portfolios")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isUnprocessableEntity());
    }

    // ── Read ──────────────────────────────────────────────────────

    @Test @Order(3)
    void getUserPortfolios_returnsCreatedPortfolio() throws Exception {
        Assumptions.assumeTrue(createdPortfolioId != null);

        mvc.perform(get("/api/v1/portfolios/user/{userId}", USER_ID))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$").isArray())
           .andExpect(jsonPath("$[0].userId").value(USER_ID));
    }

    @Test @Order(4)
    void getPortfolioById_exists_returns200() throws Exception {
        Assumptions.assumeTrue(createdPortfolioId != null);

        mvc.perform(get("/api/v1/portfolios/{id}", createdPortfolioId))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.portfolioId").value(createdPortfolioId));
    }

    @Test @Order(5)
    void getPortfolioById_notFound_returns404() throws Exception {
        mvc.perform(get("/api/v1/portfolios/{id}", UUID.randomUUID()))
           .andExpect(status().isNotFound());
    }

    // ── Rebalance ─────────────────────────────────────────────────

    @Test @Order(6)
    void rebalancePortfolio_exists_returns200() throws Exception {
        Assumptions.assumeTrue(createdPortfolioId != null);

        mvc.perform(post("/api/v1/portfolios/{id}/rebalance", createdPortfolioId))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.portfolioId").value(createdPortfolioId));
    }

    @Test @Order(7)
    void rebalancePortfolio_notFound_returns404() throws Exception {
        mvc.perform(post("/api/v1/portfolios/{id}/rebalance", UUID.randomUUID()))
           .andExpect(status().isNotFound());
    }

    // ── Health ────────────────────────────────────────────────────

    @Test @Order(8)
    void health_returnsHealthy() throws Exception {
        mvc.perform(get("/api/v1/portfolios/health"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.status").value("healthy"));
    }
}
