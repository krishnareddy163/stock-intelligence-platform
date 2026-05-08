package com.stock.user.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "users", uniqueConstraints = {@UniqueConstraint(columnNames = "email")})
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User implements UserDetails {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID userId;

    @Column(unique = true, nullable = false, length = 255)
    private String email;

    @Column(nullable = false, length = 255)
    private String name;

    @Column(nullable = false, length = 255)
    private String passwordHash;

    @Column(nullable = false, length = 20)
    @Enumerated(EnumType.STRING)
    private RiskProfile riskProfile;

    @Column(length = 100)
    private String country;

    @Column(length = 3)
    private String preferredCurrency;

    @Column(length = 20)
    @Enumerated(EnumType.STRING)
    private ExperienceLevel investmentExperience;

    @Column(nullable = false)
    private Boolean isActive;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
        this.isActive = true;
        if (this.riskProfile == null) {
            this.riskProfile = RiskProfile.MEDIUM;
        }
        if (this.preferredCurrency == null) {
            this.preferredCurrency = "USD";
        }
        if (this.investmentExperience == null) {
            this.investmentExperience = ExperienceLevel.BEGINNER;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    // UserDetails implementation
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_USER"));
    }

    @Override
    public String getPassword() {
        return this.passwordHash;
    }

    @Override
    public String getUsername() {
        return this.email;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return Boolean.TRUE.equals(this.isActive);
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return Boolean.TRUE.equals(this.isActive);
    }

    public enum RiskProfile {
        LOW, MEDIUM, HIGH
    }

    public enum ExperienceLevel {
        BEGINNER, INTERMEDIATE, ADVANCED
    }
}
