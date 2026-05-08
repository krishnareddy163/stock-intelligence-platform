package com.stock.recommendation.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.util.List;
import java.util.UUID;

@Data
public class RecommendationRequest {
    @NotBlank private String userId;
    @NotBlank private String country;
    @NotBlank private String index;
    @Positive  private double investmentAmount = 10000.0;
    private String riskProfile = "MEDIUM";
    private String timeHorizon = "LONG_TERM";
    private String strategy = "GROWTH";
    private List<String> preferredSectors = List.of();
    private String query = "Give me the best stock recommendations";
}
