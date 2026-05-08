package com.stock.portfolio.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.util.List;

@Data
public class CreatePortfolioRequest {
    @NotBlank private String userId;
    private String portfolioName = "My Portfolio";
    private List<String> symbols;
    @Positive private double totalInvestment = 10000.0;
    private String riskProfile = "MEDIUM";
    private String strategy = "GROWTH";
    private String timeHorizon = "LONG_TERM";
}
