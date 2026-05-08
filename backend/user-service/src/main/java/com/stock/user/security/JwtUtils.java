package com.stock.user.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;

@Component
@Slf4j
public class JwtUtils {

    @Value("${jwt.secret:YourVerySecureJWTSecretKeyHereWithMinimum32CharactersLength}")
    private String jwtSecret;

    @Value("${jwt.expiration:86400000}")
    private long jwtExpirationMs;

    private SecretKey getSignKey() {
        return Keys.hmacShaKeyFor(jwtSecret.getBytes());
    }

    public String generateToken(Authentication authentication) {
        return generateTokenFromUsername(authentication.getName());
    }

    public String generateTokenFromUsername(String username) {
        return Jwts.builder()
                .subject(username)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtExpirationMs))
                .signWith(getSignKey(), Jwts.SIG.HS512)
                .compact();
    }

    public String getUsernameFromJwt(String token) {
        return Jwts.parser()
                .verifyWith(getSignKey())
                .build()
                .parseSignedClaims(token)
                .getPayload()
                .getSubject();
    }

    public boolean validateJwt(String authToken) {
        try {
            Jwts.parser()
                    .verifyWith(getSignKey())
                    .build()
                    .parseSignedClaims(authToken);
            return true;
        } catch (JwtException ex) {
            log.error("Invalid JWT token: {}", ex.getMessage());
        } catch (IllegalArgumentException ex) {
            log.error("JWT claims string is empty: {}", ex.getMessage());
        }
        return false;
    }

    public long getExpirationTimeFromJwt(String token) {
        Claims claims = Jwts.parser()
                .verifyWith(getSignKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
        return (claims.getExpiration().getTime() - System.currentTimeMillis()) / 1000;
    }
}
