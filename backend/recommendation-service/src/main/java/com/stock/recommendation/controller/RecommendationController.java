package com.stock.recommendation.controller;

import com.stock.recommendation.dto.RecommendationRequest;
import com.stock.recommendation.entity.Recommendation;
import com.stock.recommendation.service.RecommendationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/v1/recommendations")
@RequiredArgsConstructor
public class RecommendationController {

    private final RecommendationService recommendationService;

    @PostMapping("/analyze")
    public ResponseEntity<Map<String, Object>> analyze(@Valid @RequestBody RecommendationRequest req) {
        log.info("Analyze request: user={}, index={}, amount={}", req.getUserId(), req.getIndex(), req.getInvestmentAmount());
        Map<String, Object> result = recommendationService.generateRecommendations(req);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/history/{userId}")
    public ResponseEntity<List<Recommendation>> getHistory(
            @PathVariable String userId,
            @RequestParam(defaultValue = "20") int limit) {
        return ResponseEntity.ok(recommendationService.getUserHistory(userId, limit));
    }

    @PostMapping("/quick-scan")
    public ResponseEntity<Map<String, Object>> quickScan(
            @RequestParam List<String> symbols,
            @RequestParam(defaultValue = "MEDIUM") String riskProfile) {
        return ResponseEntity.ok(recommendationService.quickScan(symbols, riskProfile));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "healthy", "service", "recommendation-service"));
    }
}
