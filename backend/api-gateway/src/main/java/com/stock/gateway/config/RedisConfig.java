package com.stock.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.redis.connection.ReactiveRedisConnectionFactory;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.util.Objects;

@Configuration
public class RedisConfig {

    @Bean
    @Primary
    public ReactiveRedisTemplate<String, String> reactiveRedisTemplate(
            ReactiveRedisConnectionFactory factory) {
        Objects.requireNonNull(factory, "ReactiveRedisConnectionFactory must not be null");
        StringRedisSerializer serializer = new StringRedisSerializer();
        RedisSerializationContext<String, String> context =
                RedisSerializationContext.<String, String>newSerializationContext(serializer)
                        .value(serializer)
                        .build();
        return new ReactiveRedisTemplate<>(factory, context);
    }
}
