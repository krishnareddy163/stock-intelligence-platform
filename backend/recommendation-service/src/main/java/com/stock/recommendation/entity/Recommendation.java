package com.stock.recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "recommendations")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Recommendation {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "recommendation_id")
    private UUID recommendationId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "stock_symbol", nullable = false)
    private String stockSymbol;

    @Enumerated(EnumType.STRING)
    @Column(name = "recommendation_type")
    private RecommendationType recommendationType;

    @Column(name = "score")
    private BigDecimal score;

    @Column(name = "confidence")
    private BigDecimal confidence;

    @Column(name = "reason", columnDefinition = "TEXT")
    private String reason;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "technical_indicators", columnDefinition = "TEXT")
    private String technicalIndicators;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "sentiment_data", columnDefinition = "TEXT")
    private String sentimentData;

    @Column(name = "time_horizon")
    private String timeHorizon;

    @Column(name = "target_price")
    private BigDecimal targetPrice;

    @Column(name = "stop_loss_price")
    private BigDecimal stopLossPrice;

    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level")
    private RiskLevel riskLevel;

    @CreationTimestamp
    @Column(name = "generated_at")
    private LocalDateTime generatedAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "is_acted_upon")
    private Boolean isActedUpon = false;

    public enum RecommendationType { BUY, SELL, HOLD }
    public enum RiskLevel { LOW, MEDIUM, HIGH }
}
