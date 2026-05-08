package com.stock.portfolio.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "portfolio_holdings")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PortfolioHolding {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID holdingId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "portfolio_id", nullable = false)
    private Portfolio portfolio;

    @Column(name = "stock_symbol", nullable = false)
    private String stockSymbol;

    @Column(name = "quantity", nullable = false)
    private Integer quantity;

    @Column(name = "purchase_price")
    private BigDecimal purchasePrice;

    @Column(name = "current_price")
    private BigDecimal currentPrice;

    @Column(name = "allocation_percent")
    private BigDecimal allocationPercent;

    @Column(name = "current_value")
    private BigDecimal currentValue;

    @Column(name = "target_allocation_percent")
    private BigDecimal targetAllocationPercent;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
