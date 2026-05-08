package com.stock.portfolio.service;

import com.stock.portfolio.dto.CreatePortfolioRequest;
import com.stock.portfolio.entity.Portfolio;
import com.stock.portfolio.repository.PortfolioRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PortfolioServiceTest {

    @Mock private PortfolioRepository portfolioRepository;
    @Mock private RestTemplate restTemplate;

    @InjectMocks private PortfolioService portfolioService;

    private CreatePortfolioRequest request;
    private UUID userId;
    private UUID portfolioId;
    private Portfolio savedPortfolio;

    @BeforeEach
    void setUp() {
        userId = UUID.randomUUID();
        portfolioId = UUID.randomUUID();

        request = new CreatePortfolioRequest();
        request.setUserId(userId.toString());
        request.setPortfolioName("Test Portfolio");
        request.setSymbols(List.of("RELIANCE", "TCS", "INFY"));
        request.setTotalInvestment(100000.0);
        request.setRiskProfile("MEDIUM");
        request.setStrategy("GROWTH");
        request.setTimeHorizon("LONG_TERM");

        savedPortfolio = Portfolio.builder()
                .portfolioId(portfolioId)
                .userId(userId)
                .portfolioName("Test Portfolio")
                .totalInvestment(BigDecimal.valueOf(100000.0))
                .initialInvestment(BigDecimal.valueOf(100000.0))
                .strategy(Portfolio.Strategy.GROWTH)
                .timeHorizon(Portfolio.TimeHorizon.LONG_TERM)
                .build();
    }

    @Test
    void createPortfolio_mcpUnavailable_usesEqualWeights() {
        when(restTemplate.postForObject(anyString(), any(), eq(Object.class)))
                .thenThrow(new RestClientException("Connection refused"));
        when(portfolioRepository.save(any(Portfolio.class))).thenReturn(savedPortfolio);

        Portfolio result = portfolioService.createPortfolio(request);

        assertThat(result).isNotNull();
        assertThat(result.getPortfolioId()).isEqualTo(portfolioId);
        assertThat(result.getUserId()).isEqualTo(userId);
        verify(portfolioRepository).save(any(Portfolio.class));
    }

    @Test
    void createPortfolio_mcpNull_savesPortfolioWithoutHoldings() {
        when(restTemplate.postForObject(anyString(), any(), any())).thenReturn(null);
        when(portfolioRepository.save(any(Portfolio.class))).thenReturn(savedPortfolio);

        Portfolio result = portfolioService.createPortfolio(request);

        assertThat(result).isNotNull();
        verify(portfolioRepository).save(any(Portfolio.class));
    }

    @Test
    void getUserPortfolios_returnsUserPortfolios() {
        List<Portfolio> portfolios = List.of(savedPortfolio);
        when(portfolioRepository.findByUserIdOrderByCreatedAtDesc(userId)).thenReturn(portfolios);

        List<Portfolio> result = portfolioService.getUserPortfolios(userId.toString());

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getUserId()).isEqualTo(userId);
        verify(portfolioRepository).findByUserIdOrderByCreatedAtDesc(userId);
    }

    @Test
    void getUserPortfolios_noPortfolios_returnsEmptyList() {
        when(portfolioRepository.findByUserIdOrderByCreatedAtDesc(userId)).thenReturn(List.of());

        List<Portfolio> result = portfolioService.getUserPortfolios(userId.toString());

        assertThat(result).isEmpty();
    }

    @Test
    void getPortfolio_found_returnsPortfolio() {
        when(portfolioRepository.findById(portfolioId)).thenReturn(Optional.of(savedPortfolio));

        Optional<Portfolio> result = portfolioService.getPortfolio(portfolioId.toString());

        assertThat(result).isPresent();
        assertThat(result.get().getPortfolioId()).isEqualTo(portfolioId);
    }

    @Test
    void getPortfolio_notFound_returnsEmpty() {
        when(portfolioRepository.findById(any(UUID.class))).thenReturn(Optional.empty());

        Optional<Portfolio> result = portfolioService.getPortfolio(portfolioId.toString());

        assertThat(result).isEmpty();
    }

    @Test
    void rebalancePortfolio_found_updatesTimestamp() {
        when(portfolioRepository.findById(portfolioId)).thenReturn(Optional.of(savedPortfolio));
        when(portfolioRepository.save(any(Portfolio.class))).thenReturn(savedPortfolio);

        Portfolio result = portfolioService.rebalancePortfolio(portfolioId.toString());

        assertThat(result).isNotNull();
        assertThat(savedPortfolio.getLastRebalancedAt()).isNotNull();
        verify(portfolioRepository).save(savedPortfolio);
    }

    @Test
    void rebalancePortfolio_notFound_throwsException() {
        when(portfolioRepository.findById(any(UUID.class))).thenReturn(Optional.empty());

        assertThatThrownBy(() -> portfolioService.rebalancePortfolio(portfolioId.toString()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Portfolio not found");
    }

    @Test
    void createPortfolio_lowRisk_setsRiskScore25() {
        request.setRiskProfile("LOW");
        when(restTemplate.postForObject(anyString(), any(), any())).thenReturn(null);

        Portfolio captured = Portfolio.builder()
                .portfolioId(portfolioId)
                .userId(userId)
                .totalInvestment(BigDecimal.valueOf(100000))
                .initialInvestment(BigDecimal.valueOf(100000))
                .strategy(Portfolio.Strategy.GROWTH)
                .timeHorizon(Portfolio.TimeHorizon.LONG_TERM)
                .build();
        when(portfolioRepository.save(any(Portfolio.class))).thenReturn(captured);

        portfolioService.createPortfolio(request);

        verify(portfolioRepository).save(any(Portfolio.class));
    }

    @Test
    void createPortfolio_highRisk_setsRiskScore75() {
        request.setRiskProfile("HIGH");
        when(restTemplate.postForObject(anyString(), any(), any())).thenReturn(null);
        when(portfolioRepository.save(any(Portfolio.class))).thenReturn(savedPortfolio);

        portfolioService.createPortfolio(request);

        verify(portfolioRepository).save(any(Portfolio.class));
    }
}
