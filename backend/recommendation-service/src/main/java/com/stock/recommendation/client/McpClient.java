package com.stock.recommendation.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Component
public class McpClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${mcp.orchestrator.url:http://ai-orchestrator:5000}")
    private String orchestratorUrl;

    @Value("${mcp.stock-data.url:http://stock-data-server:5001}")
    private String stockDataUrl;

    @Value("${mcp.technical.url:http://technical-analysis-server:5005}")
    private String technicalUrl;

    @Value("${mcp.alert.url:http://alert-server:5006}")
    private String alertUrl;

    public McpClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    public JsonNode callOrchestrator(Map<String, Object> request) {
        return callTool(orchestratorUrl + "/analyze", request);
    }

    public JsonNode getStockPrice(String symbol) {
        return callTool(stockDataUrl + "/tools/get_stock_price", Map.of("symbol", symbol));
    }

    public JsonNode getTechnicalIndicators(String symbol) {
        return callTool(technicalUrl + "/tools/get_technical_indicators", Map.of("symbol", symbol, "period", 14));
    }

    public JsonNode getBuySellSignals(java.util.List<String> symbols, String riskProfile) {
        return callTool(alertUrl + "/tools/generate_buy_sell_signals",
                Map.of("symbols", symbols, "risk_profile", riskProfile));
    }

    private JsonNode callTool(String url, Object body) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Object> entity = new HttpEntity<>(body, headers);
            ResponseEntity<JsonNode> response = restTemplate.exchange(url, HttpMethod.POST, entity, JsonNode.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("MCP call failed [{}]: {}", url, e.getMessage());
            try {
                return objectMapper.readTree("{\"error\": \"" + e.getMessage() + "\"}");
            } catch (Exception ex) {
                return null;
            }
        }
    }
}
