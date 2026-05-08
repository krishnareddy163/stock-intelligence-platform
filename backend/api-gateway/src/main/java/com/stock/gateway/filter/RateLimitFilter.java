package com.stock.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Slf4j
@Component
public class RateLimitFilter implements GlobalFilter, Ordered {

    private static final int MAX_REQUESTS_PER_MINUTE = 60;
    private final ReactiveRedisTemplate<String, String> redisTemplate;

    public RateLimitFilter(ReactiveRedisTemplate<String, String> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String clientIp = getClientIp(exchange);
        String key = "rate_limit:" + clientIp;

        return redisTemplate.opsForValue().increment(key)
                .flatMap(count -> {
                    if (count == 1) {
                        Duration ttl = Duration.ofMinutes(1);
                        return redisTemplate.expire(key, ttl)
                                .then(chain.filter(exchange));
                    }
                    if (count > MAX_REQUESTS_PER_MINUTE) {
                        log.warn("Rate limit exceeded for IP: {}", clientIp);
                        exchange.getResponse().setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
                        exchange.getResponse().getHeaders().add("X-RateLimit-Limit", String.valueOf(MAX_REQUESTS_PER_MINUTE));
                        exchange.getResponse().getHeaders().add("X-RateLimit-Remaining", "0");
                        return exchange.getResponse().setComplete();
                    }
                    exchange.getResponse().getHeaders().add("X-RateLimit-Remaining",
                            String.valueOf(MAX_REQUESTS_PER_MINUTE - count));
                    return chain.filter(exchange);
                })
                .onErrorResume(e -> {
                    // If Redis is down, allow request through (fail open)
                    log.warn("Rate limit Redis error: {}", e.getMessage());
                    return chain.filter(exchange);
                });
    }

    private String getClientIp(ServerWebExchange exchange) {
        String forwarded = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (forwarded != null) return forwarded.split(",")[0].trim();
        var remoteAddress = exchange.getRequest().getRemoteAddress();
        return remoteAddress != null ? remoteAddress.getAddress().getHostAddress() : "unknown";
    }

    @Override
    public int getOrder() {
        return 0;
    }
}
