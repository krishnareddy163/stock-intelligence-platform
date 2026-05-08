package com.stock.user.security;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.stock.user.repository.UserRepository;
import java.util.List;

@Service
@AllArgsConstructor
@Slf4j
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        com.stock.user.entity.User user = userRepository.findByEmailAndIsActiveTrue(email)
                .orElseThrow(() -> {
                    log.error("User not found with email: {}", email);
                    return new UsernameNotFoundException("User not found with email: " + email);
                });

        List<GrantedAuthority> authorities = List.of(
                new SimpleGrantedAuthority("ROLE_USER")
        );

        return new User(
                user.getEmail(),
                user.getPasswordHash(),
                user.getIsActive(),
                true,
                true,
                true,
                authorities
        );
    }
}
