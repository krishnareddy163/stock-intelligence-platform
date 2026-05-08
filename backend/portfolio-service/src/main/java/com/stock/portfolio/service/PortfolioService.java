package com.stock.portfolio.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.stock.portfolio.dto.CreatePortfolioRequest;
import com.stock.portfolio.entity.Portfolio;
import com.stock.portfolio.entity.PortfolioHolding;
import com.stock.portfolio.repository.PortfolioRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class PortfolioService {

    private final PortfolioRepository portfolioRepository;
    private final RestTemplate restTemplate;

    private final String portfolioMcpUrl = System.getenv().getOrDefault("MCP_PORTFOLIO_URL", "http://portfolio-server:5004");

    @Transactional
    public Portfolio createPortfolio(CreatePortfolioRequest req) {
        // Call Portfolio MCP Server for optimization
        Map<String, Object> mcpRequest = Map.of(
                "symbols", req.getSymbols(),
                "total_investment", req.getTotalInvestment(),
                "risk_profile", req.getRiskProfile(),
                "strategy", req.getStrategy()
        );

        JsonNode mcpResult = null;
        try {
            mcpResult = restTemplate.postForObject(
                    portfolioMcpUrl + "/tools/build_portfolio",
                    mcpRequest, JsonNode.class);
        } catch (Exception e) {
            log.warn("Portfolio MCP unavailable, using equal weights: {}", e.getMessage());
        }

        Portfolio portfolio = Portfolio.builder()
                .userId(UUID.fromString(req.getUserId()))
                .portfolioName(req.getPortfolioName())
                .totalInvestment(BigDecimal.valueOf(req.getTotalInvestment()))
                .initialInvestment(BigDecimal.valueOf(req.getTotalInvestment()))
                .strategy(Portfolio.Strategy.valueOf(req.getStrategy()))
                .timeHorizon(Portfolio.TimeHorizon.valueOf(req.getTimeHorizon()))
                .build();

        if (mcpResult != null && mcpResult.has("portfolio")) {
            JsonNode meta = mcpResult.get("portfolio");
            portfolio.setExpectedReturnPercent(BigDecimal.valueOf(meta.path("expected_annual_return_pct").asDouble()));
            portfolio.setRiskScore(calculateRiskScore(req.getRiskProfile()));

            List<PortfolioHolding> holdings = new ArrayList<>();
            if (mcpResult.has("holdings")) {
                mcpResult.get("holdings").forEach(h -> {
                    PortfolioHolding holding = PortfolioHolding.builder()
                            .portfolio(portfolio)
                            .stockSymbol(h.path("symbol").asText())
                            .quantity(h.path("quantity").asInt())
                            .purchasePrice(BigDecimal.valueOf(h.path("current_price").asDouble()))
                            .currentPrice(BigDecimal.valueOf(h.path("current_price").asDouble()))
                            .allocationPercent(BigDecimal.valueOf(h.path("allocation_percent").asDouble()))
                            .currentValue(BigDecimal.valueOf(h.path("actual_value").asDouble()))
                            .targetAllocationPercent(BigDecimal.valueOf(h.path("allocation_percent").asDouble()))
                            .build();
                    holdings.add(holding);
                });
            }
            portfolio.setHoldings(holdings);
        }

        Portfolio saved = portfolioRepository.save(portfolio);
        log.info("Portfolio created: id={}, user={}, holdings={}", saved.getPortfolioId(), req.getUserId(), saved.getHoldings().size());
        return saved;
    }

    public List<Portfolio> getUserPortfolios(String userId) {
        return portfolioRepository.findByUserIdOrderByCreatedAtDesc(UUID.fromString(userId));
    }

    public Optional<Portfolio> getPortfolio(String portfolioId) {
        return portfolioRepository.findById(UUID.fromString(portfolioId));
    }

    @Transactional
    public Portfolio rebalancePortfolio(String portfolioId) {
        Portfolio portfolio = portfolioRepository.findById(UUID.fromString(portfolioId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Portfolio not found: " + portfolioId));

        portfolio.setLastRebalancedAt(LocalDateTime.now());
        return portfolioRepository.save(portfolio);
    }

    private int calculateRiskScore(String riskProfile) {
        return switch (riskProfile) {
            case "LOW" -> 25;
            case "HIGH" -> 75;
            default -> 50;
        };
    }
}
