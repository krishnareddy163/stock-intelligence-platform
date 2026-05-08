package com.stock.recommendation.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.stock.recommendation.client.McpClient;
import com.stock.recommendation.dto.RecommendationRequest;
import com.stock.recommendation.entity.Recommendation;
import com.stock.recommendation.repository.RecommendationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class RecommendationService {

    private final McpClient mcpClient;
    private final RecommendationRepository repository;
    private final RedisTemplate<String, Object> redisTemplate;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public Map<String, Object> generateRecommendations(RecommendationRequest req) {
        String cacheKey = buildCacheKey(req);

        Object cached = redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            log.info("Cache hit for recommendations: {}", cacheKey);
            return (Map<String, Object>) cached;
        }

        long start = System.currentTimeMillis();
        log.info("Generating recommendations via AI Orchestrator for user={}, index={}", req.getUserId(), req.getIndex());

        Map<String, Object> orchestratorRequest = Map.of(
                "user_id", req.getUserId(),
                "query", req.getQuery(),
                "country", req.getCountry(),
                "index", req.getIndex(),
                "investment_amount", req.getInvestmentAmount(),
                "risk_profile", req.getRiskProfile(),
                "time_horizon", req.getTimeHorizon(),
                "preferred_sectors", req.getPreferredSectors(),
                "strategy", req.getStrategy()
        );

        JsonNode orchestratorResult = mcpClient.callOrchestrator(orchestratorRequest);
        long latencyMs = System.currentTimeMillis() - start;

        Map<String, Object> response = new HashMap<>();
        response.put("userId", req.getUserId());
        response.put("index", req.getIndex());
        response.put("country", req.getCountry());
        response.put("analysis", orchestratorResult != null ? orchestratorResult.path("analysis").asText() : "Analysis unavailable");
        response.put("toolCalls", orchestratorResult != null ? orchestratorResult.path("tool_calls") : Collections.emptyList());
        response.put("latencyMs", latencyMs);
        response.put("generatedAt", LocalDateTime.now().toString());

        redisTemplate.opsForValue().set(cacheKey, response, 10, TimeUnit.MINUTES);

        publishRecommendationEvent(req.getUserId(), response);
        return response;
    }

    public List<Recommendation> getUserHistory(String userId, int limit) {
        return repository.findByUserIdOrderByGeneratedAtDesc(UUID.fromString(userId))
                .stream().limit(limit).toList();
    }

    public Map<String, Object> quickScan(List<String> symbols, String riskProfile) {
        JsonNode signals = mcpClient.getBuySellSignals(symbols, riskProfile);
        return Map.of(
                "signals", signals,
                "scannedAt", LocalDateTime.now().toString()
        );
    }

    @Async
    public void publishRecommendationEvent(String userId, Map<String, Object> result) {
        try {
            kafkaTemplate.send("recommendation-generated", userId, result);
        } catch (Exception e) {
            log.warn("Kafka publish failed (non-critical): {}", e.getMessage());
        }
    }

    private String buildCacheKey(RecommendationRequest req) {
        return String.format("rec:%s:%s:%s:%s", req.getUserId(), req.getIndex(), req.getRiskProfile(), req.getTimeHorizon());
    }
}
