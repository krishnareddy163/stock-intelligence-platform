package com.stock.user;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.stock.user.dto.LoginRequest;
import com.stock.user.dto.LoginResponse;
import com.stock.user.dto.RegisterRequest;
import com.stock.user.dto.UserResponse;
import com.stock.user.entity.User;
import com.stock.user.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private UserService userService;

    private RegisterRequest registerRequest;
    private LoginRequest loginRequest;
    private UserResponse userResponse;

    @BeforeEach
    void setUp() {
        UUID userId = UUID.randomUUID();

        registerRequest = new RegisterRequest();
        registerRequest.setEmail("test@example.com");
        registerRequest.setName("Test User");
        registerRequest.setPassword("password123");
        registerRequest.setCountry("US");
        registerRequest.setRiskProfile(User.RiskProfile.MEDIUM);

        loginRequest = new LoginRequest();
        loginRequest.setEmail("test@example.com");
        loginRequest.setPassword("password123");

        userResponse = UserResponse.builder()
                .userId(userId)
                .email("test@example.com")
                .name("Test User")
                .country("US")
                .riskProfile(User.RiskProfile.MEDIUM)
                .isActive(true)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();
    }

    @Test
    void testRegisterUserSuccess() throws Exception {
        // Arrange
        when(userService.registerUser(any(RegisterRequest.class))).thenReturn(userResponse);

        // Act & Assert
        mockMvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.email").value("test@example.com"))
                .andExpect(jsonPath("$.name").value("Test User"));
    }

    @Test
    void testRegisterUserValidationError() throws Exception {
        // Arrange - Invalid email
        RegisterRequest invalidRequest = new RegisterRequest();
        invalidRequest.setEmail("invalid-email");
        invalidRequest.setName("Test User");
        invalidRequest.setPassword("password123");

        // Act & Assert
        mockMvc.perform(post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testLoginUserSuccess() throws Exception {
        // Arrange
        LoginResponse loginResponse = LoginResponse.builder()
                .token("testToken")
                .expiresIn(3600L)
                .user(userResponse)
                .build();

        when(userService.loginUser(any(LoginRequest.class))).thenReturn(loginResponse);

        // Act & Assert
        mockMvc.perform(post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("testToken"))
                .andExpect(jsonPath("$.tokenType").value("Bearer"));
    }
}
