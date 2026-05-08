package com.stock.gateway.filter;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.data.redis.core.ReactiveValueOperations;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.net.InetSocketAddress;
import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RateLimitFilterTest {

    @Mock private ReactiveRedisTemplate<String, String> redisTemplate;
    @Mock private ReactiveValueOperations<String, String> valueOps;
    @Mock private ServerWebExchange exchange;
    @Mock private ServerHttpRequest request;
    @Mock private ServerHttpResponse response;
    @Mock private HttpHeaders responseHeaders;
    @Mock private GatewayFilterChain chain;

    private RateLimitFilter filter;

    @BeforeEach
    void setUp() {
        filter = new RateLimitFilter(redisTemplate);
        when(redisTemplate.opsForValue()).thenReturn(valueOps);
        when(exchange.getRequest()).thenReturn(request);
        when(exchange.getResponse()).thenReturn(response);
        when(response.getHeaders()).thenReturn(responseHeaders);
    }

    @Test
    void getOrder_returnsZero() {
        assertThat(filter.getOrder()).isZero();
    }

    @Test
    void filter_firstRequest_setsExpiryAndAllows() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(new InetSocketAddress("10.0.0.1", 1234));
        when(valueOps.increment("rate_limit:10.0.0.1")).thenReturn(Mono.just(1L));
        when(redisTemplate.expire(eq("rate_limit:10.0.0.1"), any(Duration.class)))
                .thenReturn(Mono.just(true));
        when(chain.filter(exchange)).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(redisTemplate).expire(eq("rate_limit:10.0.0.1"), eq(Duration.ofMinutes(1)));
        verify(chain).filter(exchange);
    }

    @Test
    void filter_withinLimit_addsRemainingHeaderAndAllows() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(new InetSocketAddress("10.0.0.2", 1234));
        when(valueOps.increment("rate_limit:10.0.0.2")).thenReturn(Mono.just(30L));
        when(chain.filter(exchange)).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(responseHeaders).add("X-RateLimit-Remaining", "30");
        verify(chain).filter(exchange);
    }

    @Test
    void filter_exceedsLimit_returns429() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(new InetSocketAddress("10.0.0.3", 1234));
        when(valueOps.increment("rate_limit:10.0.0.3")).thenReturn(Mono.just(61L));
        when(response.setStatusCode(HttpStatus.TOO_MANY_REQUESTS)).thenReturn(true);
        when(response.setComplete()).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(response).setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
        verify(responseHeaders).add("X-RateLimit-Limit", "60");
        verify(responseHeaders).add("X-RateLimit-Remaining", "0");
        verifyNoInteractions(chain);
    }

    @Test
    void filter_exactlyAtLimit_returns429() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(new InetSocketAddress("10.0.0.4", 1234));
        when(valueOps.increment("rate_limit:10.0.0.4")).thenReturn(Mono.just(61L));
        when(response.setStatusCode(any())).thenReturn(true);
        when(response.setComplete()).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(response).setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
    }

    @Test
    void filter_xForwardedForHeader_usesForwardedIp() {
        HttpHeaders headers = new HttpHeaders();
        headers.add("X-Forwarded-For", "203.0.113.5, 10.0.0.1");
        when(request.getHeaders()).thenReturn(headers);
        when(valueOps.increment("rate_limit:203.0.113.5")).thenReturn(Mono.just(1L));
        when(redisTemplate.expire(anyString(), any(Duration.class))).thenReturn(Mono.just(true));
        when(chain.filter(exchange)).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(valueOps).increment("rate_limit:203.0.113.5");
    }

    @Test
    void filter_redisError_failsOpenAndAllows() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(new InetSocketAddress("10.0.0.5", 1234));
        when(valueOps.increment(anyString())).thenReturn(Mono.error(new RuntimeException("Redis down")));
        when(chain.filter(exchange)).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(chain).filter(exchange);
        verify(response, never()).setStatusCode(any());
    }

    @Test
    void filter_noRemoteAddress_usesUnknownKey() {
        when(request.getHeaders()).thenReturn(HttpHeaders.EMPTY);
        when(request.getRemoteAddress()).thenReturn(null);
        when(valueOps.increment("rate_limit:unknown")).thenReturn(Mono.just(1L));
        when(redisTemplate.expire(anyString(), any(Duration.class))).thenReturn(Mono.just(true));
        when(chain.filter(exchange)).thenReturn(Mono.empty());

        StepVerifier.create(filter.filter(exchange, chain))
                .verifyComplete();

        verify(valueOps).increment("rate_limit:unknown");
    }
}
