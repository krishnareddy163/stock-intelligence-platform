package com.stock.portfolio.repository;

import com.stock.portfolio.entity.Portfolio;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface PortfolioRepository extends JpaRepository<Portfolio, UUID> {
    List<Portfolio> findByUserIdOrderByCreatedAtDesc(UUID userId);
}
