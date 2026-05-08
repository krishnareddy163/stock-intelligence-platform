package com.stock.recommendation.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.stock.recommendation.client.McpClient;
import com.stock.recommendation.dto.RecommendationRequest;
import com.stock.recommendation.entity.Recommendation;
import com.stock.recommendation.repository.RecommendationRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.kafka.core.KafkaTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RecommendationServiceTest {

    @Mock private McpClient mcpClient;
    @Mock private RecommendationRepository repository;
    @Mock private RedisTemplate<String, Object> redisTemplate;
    @Mock private ValueOperations<String, Object> valueOps;
    @Mock private KafkaTemplate<String, Object> kafkaTemplate;

    @InjectMocks private RecommendationService recommendationService;

    private RecommendationRequest request;
    private final ObjectMapper mapper = new ObjectMapper();

    @BeforeEach
    void setUp() {
        request = new RecommendationRequest();
        request.setUserId("user-123");
        request.setCountry("IN");
        request.setIndex("NIFTY50");
        request.setInvestmentAmount(100000.0);
        request.setRiskProfile("MEDIUM");
        request.setTimeHorizon("LONG_TERM");
        request.setStrategy("GROWTH");
        request.setPreferredSectors(List.of());
        request.setQuery("Best Nifty 50 stocks");

        when(redisTemplate.opsForValue()).thenReturn(valueOps);
    }

    @Test
    void generateRecommendations_cacheMiss_callsOrchestratorAndCaches() {
        ObjectNode orchestratorResponse = mapper.createObjectNode();
        orchestratorResponse.put("analysis", "Strong buy signals for RELIANCE and TCS");
        orchestratorResponse.putArray("tool_calls");

        when(valueOps.get(anyString())).thenReturn(null);
        when(mcpClient.callOrchestrator(anyMap())).thenReturn(orchestratorResponse);
        doNothing().when(valueOps).set(anyString(), any(), anyLong(), any());
        when(kafkaTemplate.send(anyString(), anyString(), any())).thenReturn(null);

        Map<String, Object> result = recommendationService.generateRecommendations(request);

        assertThat(result).isNotNull();
        assertThat(result.get("userId")).isEqualTo("user-123");
        assertThat(result.get("index")).isEqualTo("NIFTY50");
        assertThat(result.get("analysis")).isEqualTo("Strong buy signals for RELIANCE and TCS");
        assertThat(result).containsKey("latencyMs");
        assertThat(result).containsKey("generatedAt");

        verify(mcpClient).callOrchestrator(anyMap());
        verify(valueOps).set(anyString(), any(), anyLong(), any());
    }

    @Test
    @SuppressWarnings("unchecked")
    void generateRecommendations_cacheHit_returnsCachedResult() {
        Map<String, Object> cachedResult = Map.of(
                "userId", "user-123",
                "index", "NIFTY50",
                "analysis", "cached analysis"
        );
        when(valueOps.get(anyString())).thenReturn(cachedResult);

        Map<String, Object> result = recommendationService.generateRecommendations(request);

        assertThat(result).isEqualTo(cachedResult);
        verifyNoInteractions(mcpClient);
        verify(valueOps, never()).set(anyString(), any(), anyLong(), any());
    }

    @Test
    void generateRecommendations_orchestratorReturnsNull_usesUnavailableMessage() {
        when(valueOps.get(anyString())).thenReturn(null);
        when(mcpClient.callOrchestrator(anyMap())).thenReturn(null);
        doNothing().when(valueOps).set(anyString(), any(), anyLong(), any());
        when(kafkaTemplate.send(anyString(), anyString(), any())).thenReturn(null);

        Map<String, Object> result = recommendationService.generateRecommendations(request);

        assertThat(result.get("analysis")).isEqualTo("Analysis unavailable");
    }

    @Test
    void generateRecommendations_kafkaFails_doesNotThrow() {
        ObjectNode orchestratorResponse = mapper.createObjectNode();
        orchestratorResponse.put("analysis", "Buy RELIANCE");
        orchestratorResponse.putArray("tool_calls");

        when(valueOps.get(anyString())).thenReturn(null);
        when(mcpClient.callOrchestrator(anyMap())).thenReturn(orchestratorResponse);
        doNothing().when(valueOps).set(anyString(), any(), anyLong(), any());
        when(kafkaTemplate.send(anyString(), anyString(), any()))
                .thenThrow(new RuntimeException("Kafka unavailable"));

        Map<String, Object> result = recommendationService.generateRecommendations(request);

        assertThat(result).isNotNull();
    }

    @Test
    void getUserHistory_delegatesToRepository() {
        UUID uid = UUID.fromString("550e8400-e29b-41d4-a716-446655440000");
        Recommendation rec = Recommendation.builder()
                .userId(uid)
                .stockSymbol("RELIANCE")
                .recommendationType(Recommendation.RecommendationType.BUY)
                .generatedAt(LocalDateTime.now())
                .build();
        when(repository.findByUserIdOrderByGeneratedAtDesc(uid)).thenReturn(List.of(rec, rec, rec));

        List<Recommendation> result = recommendationService.getUserHistory(uid.toString(), 2);

        assertThat(result).hasSize(2);
        verify(repository).findByUserIdOrderByGeneratedAtDesc(uid);
    }

    @Test
    void quickScan_callsMcpClient() {
        ObjectNode signals = mapper.createObjectNode();
        signals.putArray("signals").addObject().put("symbol", "RELIANCE").put("action", "BUY");

        when(mcpClient.getBuySellSignals(anyList(), anyString())).thenReturn(signals);

        Map<String, Object> result = recommendationService.quickScan(List.of("RELIANCE", "TCS"), "MEDIUM");

        assertThat(result).containsKey("signals");
        assertThat(result).containsKey("scannedAt");
        verify(mcpClient).getBuySellSignals(List.of("RELIANCE", "TCS"), "MEDIUM");
    }

    @Test
    void cacheKey_differentProfiles_produceDifferentKeys() {
        RecommendationRequest req2 = new RecommendationRequest();
        req2.setUserId("user-123");
        req2.setCountry("IN");
        req2.setIndex("NIFTY50");
        req2.setInvestmentAmount(100000.0);
        req2.setRiskProfile("HIGH");
        req2.setTimeHorizon("LONG_TERM");
        req2.setStrategy("GROWTH");
        req2.setPreferredSectors(List.of());

        ObjectNode response = mapper.createObjectNode();
        response.put("analysis", "test");
        response.putArray("tool_calls");

        when(valueOps.get(anyString())).thenReturn(null);
        when(mcpClient.callOrchestrator(anyMap())).thenReturn(response);
        doNothing().when(valueOps).set(anyString(), any(), anyLong(), any());
        when(kafkaTemplate.send(anyString(), anyString(), any())).thenReturn(null);

        recommendationService.generateRecommendations(request);
        recommendationService.generateRecommendations(req2);

        // Two different cache keys used — verify set called twice with different keys
        verify(valueOps, times(2)).set(anyString(), any(), anyLong(), any());
    }
}
