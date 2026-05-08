package com.stock.user.service;

import com.stock.user.dto.LoginRequest;
import com.stock.user.dto.RegisterRequest;
import com.stock.user.entity.User;
import com.stock.user.exception.InvalidCredentialsException;
import com.stock.user.exception.UserAlreadyExistsException;
import com.stock.user.exception.UserNotFoundException;
import com.stock.user.repository.UserRepository;
import com.stock.user.security.JwtUtils;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private AuthenticationManager authenticationManager;

    @Mock
    private JwtUtils jwtUtils;

    @InjectMocks
    private UserService userService;

    private RegisterRequest registerRequest;
    private LoginRequest loginRequest;
    private User user;
    private UUID userId;

    @BeforeEach
    void setUp() {
        userId = UUID.randomUUID();

        registerRequest = new RegisterRequest();
        registerRequest.setEmail("test@example.com");
        registerRequest.setName("Test User");
        registerRequest.setPassword("password123");
        registerRequest.setCountry("US");
        registerRequest.setRiskProfile(User.RiskProfile.MEDIUM);

        loginRequest = new LoginRequest();
        loginRequest.setEmail("test@example.com");
        loginRequest.setPassword("password123");

        user = User.builder()
                .userId(userId)
                .email("test@example.com")
                .name("Test User")
                .passwordHash("hashedPassword")
                .country("US")
                .riskProfile(User.RiskProfile.MEDIUM)
                .isActive(true)
                .build();
    }

    @Test
    void testRegisterUserSuccess() {
        // Arrange
        when(userRepository.existsByEmail(registerRequest.getEmail())).thenReturn(false);
        when(passwordEncoder.encode(registerRequest.getPassword())).thenReturn("hashedPassword");
        when(userRepository.save(any(User.class))).thenReturn(user);

        // Act
        var response = userService.registerUser(registerRequest);

        // Assert
        assertNotNull(response);
        assertEquals(registerRequest.getEmail(), response.getEmail());
        assertEquals(registerRequest.getName(), response.getName());
        verify(userRepository, times(1)).save(any(User.class));
    }

    @Test
    void testRegisterUserAlreadyExists() {
        // Arrange
        when(userRepository.existsByEmail(registerRequest.getEmail())).thenReturn(true);

        // Act & Assert
        assertThrows(UserAlreadyExistsException.class, () -> userService.registerUser(registerRequest));
        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    void testLoginUserSuccess() {
        // Arrange
        Authentication authentication = mock(Authentication.class);
        when(authentication.getName()).thenReturn("test@example.com");

        when(authenticationManager.authenticate(any(UsernamePasswordAuthenticationToken.class)))
                .thenReturn(authentication);
        when(jwtUtils.generateToken(authentication)).thenReturn("testToken");
        when(jwtUtils.getExpirationTimeFromJwt("testToken")).thenReturn(3600L);
        when(userRepository.findByEmailAndIsActiveTrue("test@example.com")).thenReturn(Optional.of(user));

        // Act
        var response = userService.loginUser(loginRequest);

        // Assert
        assertNotNull(response);
        assertEquals("testToken", response.getToken());
        assertEquals("Bearer", response.getTokenType());
        assertNotNull(response.getUser());
        verify(authenticationManager, times(1)).authenticate(any(UsernamePasswordAuthenticationToken.class));
    }

    @Test
    void testLoginUserInvalidCredentials() {
        // Arrange
        when(authenticationManager.authenticate(any(UsernamePasswordAuthenticationToken.class)))
                .thenThrow(new BadCredentialsException("Invalid credentials"));

        // Act & Assert
        assertThrows(InvalidCredentialsException.class, () -> userService.loginUser(loginRequest));
    }

    @Test
    void testGetUserByIdSuccess() {
        // Arrange
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));

        // Act
        var response = userService.getUserById(userId);

        // Assert
        assertNotNull(response);
        assertEquals(userId, response.getUserId());
        assertEquals(user.getEmail(), response.getEmail());
        verify(userRepository, times(1)).findById(userId);
    }

    @Test
    void testGetUserByIdNotFound() {
        // Arrange
        when(userRepository.findById(userId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(UserNotFoundException.class, () -> userService.getUserById(userId));
    }

    @Test
    void testGetUserByEmailSuccess() {
        // Arrange
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(user));

        // Act
        var response = userService.getUserByEmail("test@example.com");

        // Assert
        assertNotNull(response);
        assertEquals(user.getEmail(), response.getEmail());
        verify(userRepository, times(1)).findByEmail("test@example.com");
    }

    @Test
    void testChangePasswordSuccess() {
        // Arrange
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("password123", user.getPasswordHash())).thenReturn(true);
        when(passwordEncoder.encode("newPassword123")).thenReturn("newHashedPassword");
        when(userRepository.save(any(User.class))).thenReturn(user);

        // Act
        assertDoesNotThrow(() -> userService.changePassword(userId, "password123", "newPassword123"));

        // Assert
        verify(userRepository, times(1)).save(any(User.class));
    }

    @Test
    void testChangePasswordInvalidOldPassword() {
        // Arrange
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        when(passwordEncoder.matches("wrongPassword", user.getPasswordHash())).thenReturn(false);

        // Act & Assert
        assertThrows(InvalidCredentialsException.class, 
                () -> userService.changePassword(userId, "wrongPassword", "newPassword123"));
        verify(userRepository, never()).save(any(User.class));
    }

    @Test
    void testDeactivateUserSuccess() {
        // Arrange
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        when(userRepository.save(any(User.class))).thenReturn(user);

        // Act
        assertDoesNotThrow(() -> userService.deactivateUser(userId));

        // Assert
        assertFalse(user.getIsActive());
        verify(userRepository, times(1)).save(any(User.class));
    }
}
