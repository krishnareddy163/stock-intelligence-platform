package com.stock.user.service;

import com.stock.user.dto.LoginRequest;
import com.stock.user.dto.LoginResponse;
import com.stock.user.dto.RegisterRequest;
import com.stock.user.dto.UserResponse;
import com.stock.user.entity.User;
import com.stock.user.exception.InvalidCredentialsException;
import com.stock.user.exception.UserAlreadyExistsException;
import com.stock.user.exception.UserNotFoundException;
import com.stock.user.repository.UserRepository;
import com.stock.user.security.JwtUtils;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@AllArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtUtils jwtUtils;

    /**
     * Register a new user
     */
    @Transactional
    public UserResponse registerUser(RegisterRequest registerRequest) {
        log.info("Registering new user: {}", registerRequest.getEmail());

        // Check if user already exists
        if (userRepository.existsByEmail(registerRequest.getEmail())) {
            log.warn("User already exists with email: {}", registerRequest.getEmail());
            throw new UserAlreadyExistsException("User already exists with email: " + registerRequest.getEmail());
        }

        // Create new user
        User user = User.builder()
                .email(registerRequest.getEmail())
                .name(registerRequest.getName())
                .passwordHash(passwordEncoder.encode(registerRequest.getPassword()))
                .riskProfile(registerRequest.getRiskProfile() != null
                        ? registerRequest.getRiskProfile()
                        : User.RiskProfile.MEDIUM)
                .country(registerRequest.getCountry())
                .preferredCurrency(registerRequest.getPreferredCurrency() != null
                        ? registerRequest.getPreferredCurrency()
                        : "USD")
                .investmentExperience(registerRequest.getInvestmentExperience() != null
                        ? registerRequest.getInvestmentExperience()
                        : User.ExperienceLevel.BEGINNER)
                .isActive(true)
                .build();

        User savedUser = userRepository.save(user);
        log.info("User registered successfully with ID: {}", savedUser.getUserId());

        return UserResponse.fromEntity(savedUser);
    }

    /**
     * Login user and return JWT token
     */
    public LoginResponse loginUser(LoginRequest loginRequest) {
        log.info("Authenticating user: {}", loginRequest.getEmail());

        try {
            // Authenticate user
            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            loginRequest.getEmail(),
                            loginRequest.getPassword()
                    )
            );

            SecurityContextHolder.getContext().setAuthentication(authentication);

            // Generate JWT token
            String token = jwtUtils.generateToken(authentication);
            long expiresIn = jwtUtils.getExpirationTimeFromJwt(token);

            // Get user details
            User user = userRepository.findByEmailAndIsActiveTrue(loginRequest.getEmail())
                    .orElseThrow(() -> new UserNotFoundException("User not found"));

            log.info("User authenticated successfully: {}", loginRequest.getEmail());

            return LoginResponse.builder()
                    .token(token)
                    .tokenType("Bearer")
                    .expiresIn(expiresIn)
                    .user(UserResponse.fromEntity(user))
                    .build();

        } catch (BadCredentialsException e) {
            log.warn("Invalid credentials for user: {}", loginRequest.getEmail());
            throw new InvalidCredentialsException("Invalid email or password");
        }
    }

    /**
     * Get user by ID
     */
    public UserResponse getUserById(UUID userId) {
        log.debug("Fetching user with ID: {}", userId);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> {
                    log.warn("User not found with ID: {}", userId);
                    return new UserNotFoundException("User not found with ID: " + userId);
                });

        return UserResponse.fromEntity(user);
    }

    /**
     * Get user by email
     */
    public UserResponse getUserByEmail(String email) {
        log.debug("Fetching user with email: {}", email);

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> {
                    log.warn("User not found with email: {}", email);
                    return new UserNotFoundException("User not found with email: " + email);
                });

        return UserResponse.fromEntity(user);
    }

    /**
     * Update user profile
     */
    @Transactional
    public UserResponse updateUserProfile(UUID userId, RegisterRequest updateRequest) {
        log.info("Updating user profile: {}", userId);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> {
                    log.warn("User not found with ID: {}", userId);
                    return new UserNotFoundException("User not found with ID: " + userId);
                });

        // Update fields
        if (updateRequest.getName() != null && !updateRequest.getName().isEmpty()) {
            user.setName(updateRequest.getName());
        }
        if (updateRequest.getRiskProfile() != null) {
            user.setRiskProfile(updateRequest.getRiskProfile());
        }
        if (updateRequest.getCountry() != null) {
            user.setCountry(updateRequest.getCountry());
        }
        if (updateRequest.getPreferredCurrency() != null) {
            user.setPreferredCurrency(updateRequest.getPreferredCurrency());
        }
        if (updateRequest.getInvestmentExperience() != null) {
            user.setInvestmentExperience(updateRequest.getInvestmentExperience());
        }

        User updatedUser = userRepository.save(user);
        log.info("User profile updated successfully: {}", userId);

        return UserResponse.fromEntity(updatedUser);
    }

    /**
     * Change user password
     */
    @Transactional
    public void changePassword(UUID userId, String oldPassword, String newPassword) {
        log.info("Changing password for user: {}", userId);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("User not found with ID: " + userId));

        // Verify old password
        if (!passwordEncoder.matches(oldPassword, user.getPasswordHash())) {
            log.warn("Invalid old password for user: {}", userId);
            throw new InvalidCredentialsException("Invalid old password");
        }

        // Update password
        user.setPasswordHash(passwordEncoder.encode(newPassword));
        userRepository.save(user);

        log.info("Password changed successfully for user: {}", userId);
    }

    /**
     * Deactivate user account
     */
    @Transactional
    public void deactivateUser(UUID userId) {
        log.info("Deactivating user: {}", userId);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("User not found with ID: " + userId));

        user.setIsActive(false);
        userRepository.save(user);

        log.info("User deactivated successfully: {}", userId);
    }
}
