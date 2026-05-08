package com.stock.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Base64;
import java.util.List;

@Slf4j
@Component
public class JwtAuthFilter implements GlobalFilter, Ordered {

    private static final List<String> PUBLIC_PATHS = List.of(
            "/api/v1/auth/",
            "/health",
            "/actuator/",
            "/api/v1/stocks/public"
    );

    @Value("${jwt.secret:default-secret-change-in-production}")
    private String jwtSecret;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();

        if (isPublicPath(path)) {
            return chain.filter(exchange);
        }

        String authHeader = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        String token = authHeader.substring(7);
        if (!isValidToken(token)) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        String userId = extractUserId(token);
        ServerWebExchange mutated = exchange.mutate()
                .request(r -> r.header("X-User-Id", userId))
                .build();

        return chain.filter(mutated);
    }

    private boolean isPublicPath(String path) {
        return PUBLIC_PATHS.stream().anyMatch(path::startsWith);
    }

    private boolean isValidToken(String token) {
        // Production: use proper JWT validation with jjwt
        // This is a structural placeholder — real validation uses JwtUtils
        try {
            String[] parts = token.split("\\.");
            return parts.length == 3;
        } catch (Exception e) {
            return false;
        }
    }

    private String extractUserId(String token) {
        try {
            String payload = new String(Base64.getUrlDecoder().decode(token.split("\\.")[1]));
            // Extract "sub" from JSON payload (simplified — use Jackson in production)
            int subIdx = payload.indexOf("\"sub\":\"");
            if (subIdx == -1) return "unknown";
            int start = subIdx + 7;
            int end = payload.indexOf("\"", start);
            return payload.substring(start, end);
        } catch (Exception e) {
            return "unknown";
        }
    }

    @Override
    public int getOrder() {
        return -1;
    }
}
