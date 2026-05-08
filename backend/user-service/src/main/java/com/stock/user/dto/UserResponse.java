package com.stock.user.dto;

import com.stock.user.entity.User;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserResponse {

    private UUID userId;
    private String email;
    private String name;
    private User.RiskProfile riskProfile;
    private String country;
    private String preferredCurrency;
    private User.ExperienceLevel investmentExperience;
    private Boolean isActive;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /**
     * Convert User entity to UserResponse DTO
     */
    public static UserResponse fromEntity(User user) {
        return UserResponse.builder()
                .userId(user.getUserId())
                .email(user.getEmail())
                .name(user.getName())
                .riskProfile(user.getRiskProfile())
                .country(user.getCountry())
                .preferredCurrency(user.getPreferredCurrency())
                .investmentExperience(user.getInvestmentExperience())
                .isActive(user.getIsActive())
                .createdAt(user.getCreatedAt())
                .updatedAt(user.getUpdatedAt())
                .build();
    }
}
