package com.stock.user.controller;

import com.stock.user.dto.LoginRequest;
import com.stock.user.dto.LoginResponse;
import com.stock.user.dto.RegisterRequest;
import com.stock.user.dto.UserResponse;
import com.stock.user.service.UserService;
import jakarta.validation.Valid;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/auth")
@AllArgsConstructor
@Slf4j
public class AuthController {

    private final UserService userService;

    /**
     * User registration endpoint
     * POST /auth/register
     */
    @PostMapping("/register")
    public ResponseEntity<UserResponse> register(@Valid @RequestBody RegisterRequest registerRequest) {
        log.info("Register request for email: {}", registerRequest.getEmail());
        UserResponse response = userService.registerUser(registerRequest);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * User login endpoint
     * POST /auth/login
     */
    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest loginRequest) {
        log.info("Login request for email: {}", loginRequest.getEmail());
        LoginResponse response = userService.loginUser(loginRequest);
        return ResponseEntity.ok(response);
    }

    /**
     * Get current user profile
     * GET /auth/me
     */
    @GetMapping("/me")
    public ResponseEntity<UserResponse> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        log.info("Fetching current user profile: {}", email);
        UserResponse response = userService.getUserByEmail(email);
        return ResponseEntity.ok(response);
    }

    /**
     * Get user by ID
     * GET /auth/users/{userId}
     */
    @GetMapping("/users/{userId}")
    public ResponseEntity<UserResponse> getUserById(@PathVariable UUID userId) {
        log.info("Fetching user: {}", userId);
        UserResponse response = userService.getUserById(userId);
        return ResponseEntity.ok(response);
    }

    /**
     * Update user profile
     * PUT /auth/profile
     */
    @PutMapping("/profile")
    public ResponseEntity<UserResponse> updateProfile(@Valid @RequestBody RegisterRequest updateRequest) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        log.info("Updating profile for user: {}", email);

        // Get user ID from email
        UserResponse currentUser = userService.getUserByEmail(email);
        UserResponse response = userService.updateUserProfile(currentUser.getUserId(), updateRequest);
        return ResponseEntity.ok(response);
    }

    /**
     * Change password
     * POST /auth/change-password
     */
    @PostMapping("/change-password")
    public ResponseEntity<String> changePassword(
            @RequestParam String oldPassword,
            @RequestParam String newPassword) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        log.info("Changing password for user: {}", email);

        UserResponse currentUser = userService.getUserByEmail(email);
        userService.changePassword(currentUser.getUserId(), oldPassword, newPassword);
        return ResponseEntity.ok("Password changed successfully");
    }

    /**
     * Deactivate user account
     * DELETE /auth/account
     */
    @DeleteMapping("/account")
    public ResponseEntity<String> deactivateAccount() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();
        log.info("Deactivating account for user: {}", email);

        UserResponse currentUser = userService.getUserByEmail(email);
        userService.deactivateUser(currentUser.getUserId());
        return ResponseEntity.ok("Account deactivated successfully");
    }
}
