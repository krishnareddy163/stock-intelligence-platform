package com.stock.portfolio.controller;

import com.stock.portfolio.dto.CreatePortfolioRequest;
import com.stock.portfolio.entity.Portfolio;
import com.stock.portfolio.service.PortfolioService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/portfolios")
@RequiredArgsConstructor
public class PortfolioController {

    private final PortfolioService portfolioService;

    @PostMapping
    public ResponseEntity<Portfolio> create(@Valid @RequestBody CreatePortfolioRequest req) {
        return ResponseEntity.ok(portfolioService.createPortfolio(req));
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Portfolio>> getUserPortfolios(@PathVariable String userId) {
        return ResponseEntity.ok(portfolioService.getUserPortfolios(userId));
    }

    @GetMapping("/{portfolioId}")
    public ResponseEntity<Portfolio> getPortfolio(@PathVariable String portfolioId) {
        return portfolioService.getPortfolio(portfolioId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{portfolioId}/rebalance")
    public ResponseEntity<Portfolio> rebalance(@PathVariable String portfolioId) {
        return ResponseEntity.ok(portfolioService.rebalancePortfolio(portfolioId));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "healthy", "service", "portfolio-service"));
    }
}
