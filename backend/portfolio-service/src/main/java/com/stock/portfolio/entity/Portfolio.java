package com.stock.portfolio.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "portfolios")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Portfolio {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID portfolioId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "portfolio_name")
    private String portfolioName;

    @Column(name = "total_investment", nullable = false)
    private BigDecimal totalInvestment;

    @Column(name = "initial_investment", nullable = false)
    private BigDecimal initialInvestment;

    @Column(name = "current_value")
    private BigDecimal currentValue;

    @Column(name = "risk_score")
    private Integer riskScore;

    @Column(name = "expected_return_percent")
    private BigDecimal expectedReturnPercent;

    @Enumerated(EnumType.STRING)
    @Column(name = "strategy")
    private Strategy strategy;

    @Enumerated(EnumType.STRING)
    @Column(name = "time_horizon")
    private TimeHorizon timeHorizon;

    @Column(name = "last_rebalanced_at")
    private LocalDateTime lastRebalancedAt;

    @CreationTimestamp
    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @OneToMany(mappedBy = "portfolio", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @Builder.Default
    private List<PortfolioHolding> holdings = new ArrayList<>();

    public enum Strategy { GROWTH, VALUE, DIVIDEND, MOMENTUM, HYBRID }
    public enum TimeHorizon { INTRADAY, SHORT_TERM, MID_TERM, LONG_TERM }
}
