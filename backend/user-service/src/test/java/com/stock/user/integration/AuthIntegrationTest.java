package com.stock.user.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.user.dto.LoginRequest;
import com.stock.user.dto.RegisterRequest;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class AuthIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper objectMapper;

    private static final String EMAIL = "integration@stockiq.test";
    private static final String PASSWORD = "SecurePass123!";
    private static String jwtToken;

    // ── Register ─────────────────────────────────────────────────

    @Test @Order(1)
    void register_newUser_returns201WithProfile() throws Exception {
        var req = new RegisterRequest();
        req.setEmail(EMAIL);
        req.setName("Integration User");
        req.setPassword(PASSWORD);
        req.setCountry("IN");

        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isCreated())
           .andExpect(jsonPath("$.email").value(EMAIL))
           .andExpect(jsonPath("$.name").value("Integration User"))
           .andExpect(jsonPath("$.password").doesNotExist());
    }

    @Test @Order(2)
    void register_duplicateEmail_returns409() throws Exception {
        var req = new RegisterRequest();
        req.setEmail(EMAIL);
        req.setName("Dup User");
        req.setPassword(PASSWORD);

        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isConflict());
    }

    @Test @Order(3)
    void register_invalidEmail_returns400() throws Exception {
        var req = new RegisterRequest();
        req.setEmail("not-an-email");
        req.setName("Bad User");
        req.setPassword(PASSWORD);

        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isBadRequest());
    }

    @Test @Order(4)
    void register_shortPassword_returns400() throws Exception {
        var req = new RegisterRequest();
        req.setEmail("short@test.com");
        req.setName("Short Pass");
        req.setPassword("abc");

        mvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isBadRequest());
    }

    // ── Login ─────────────────────────────────────────────────────

    @Test @Order(5)
    void login_validCredentials_returnsJwtToken() throws Exception {
        var req = new LoginRequest();
        req.setEmail(EMAIL);
        req.setPassword(PASSWORD);

        var result = mvc.perform(post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.token").isNotEmpty())
           .andExpect(jsonPath("$.email").value(EMAIL))
           .andReturn();

        var body = objectMapper.readTree(result.getResponse().getContentAsString());
        jwtToken = body.get("token").asText();
    }

    @Test @Order(6)
    void login_wrongPassword_returns401() throws Exception {
        var req = new LoginRequest();
        req.setEmail(EMAIL);
        req.setPassword("WrongPassword!");

        mvc.perform(post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isUnauthorized());
    }

    @Test @Order(7)
    void login_unknownEmail_returns401() throws Exception {
        var req = new LoginRequest();
        req.setEmail("nobody@test.com");
        req.setPassword(PASSWORD);

        mvc.perform(post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
           .andExpect(status().isUnauthorized());
    }

    // ── Protected endpoint ────────────────────────────────────────

    @Test @Order(8)
    void getMe_withValidToken_returnsUserProfile() throws Exception {
        Assumptions.assumeTrue(jwtToken != null, "Skipped: login test must pass first");

        mvc.perform(get("/auth/me")
                .header("Authorization", "Bearer " + jwtToken))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.email").value(EMAIL));
    }

    @Test @Order(9)
    void getMe_withoutToken_returns403() throws Exception {
        mvc.perform(get("/auth/me"))
           .andExpect(status().isForbidden());
    }

    @Test @Order(10)
    void getMe_withExpiredToken_returns403() throws Exception {
        String bogusToken = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjoxfQ.invalid";
        mvc.perform(get("/auth/me")
                .header("Authorization", "Bearer " + bogusToken))
           .andExpect(status().isForbidden());
    }

    // ── Health ────────────────────────────────────────────────────

    @Test @Order(11)
    void health_returnsUp() throws Exception {
        mvc.perform(get("/health"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.status").value("UP"));
    }
}
