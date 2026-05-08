package com.stock.recommendation.repository;

import com.stock.recommendation.entity.Recommendation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface RecommendationRepository extends JpaRepository<Recommendation, UUID> {
    List<Recommendation> findByUserIdOrderByGeneratedAtDesc(UUID userId);
    List<Recommendation> findByStockSymbolOrderByGeneratedAtDesc(String stockSymbol);
}
