# User Service

Spring Boot microservice for user authentication and profile management in the Stock Market Intelligence Platform.

## Overview

The User Service handles:
- **User Registration** — Email, password, risk profile, experience level
- **User Authentication** — Login with JWT token generation
- **Profile Management** — Get, update user profile
- **Account Security** — Password change, account deactivation
- **JWT Token** — Stateless authentication with token refresh support

## Technologies

- **Spring Boot 3.2**
- **Spring Security** — JWT authentication
- **PostgreSQL** — User data persistence
- **JWT (io.jsonwebtoken)** — Token management
- **Lombok** — Boilerplate reduction
- **JUnit 5 + Mockito** — Testing

## API Endpoints

### Authentication

#### Register User
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "SecurePassword123!",
  "country": "US",
  "riskProfile": "MEDIUM",
  "investmentExperience": "BEGINNER"
}

Response: 201 Created
{
  "userId": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "riskProfile": "MEDIUM",
  "country": "US",
  "createdAt": "2024-05-07T10:30:00"
}
```

#### Login User
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response: 200 OK
{
  "token": "eyJhbGciOiJIUzUxMiJ9...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "user": { ... }
}
```

### User Profile

#### Get Current User
```bash
GET /auth/me
Authorization: Bearer <token>

Response: 200 OK
{
  "userId": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  ...
}
```

#### Get User by ID
```bash
GET /auth/users/{userId}
Authorization: Bearer <token>

Response: 200 OK { ... }
```

#### Update Profile
```bash
PUT /auth/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Doe",
  "riskProfile": "HIGH",
  "country": "UK"
}

Response: 200 OK { ... }
```

#### Change Password
```bash
POST /auth/change-password?oldPassword=old&newPassword=new
Authorization: Bearer <token>

Response: 200 OK
"Password changed successfully"
```

#### Deactivate Account
```bash
DELETE /auth/account
Authorization: Bearer <token>

Response: 200 OK
"Account deactivated successfully"
```

## Setup & Running

### Prerequisites
- Java 17+
- PostgreSQL running
- Maven 3.9+

### Configuration

Update `src/main/resources/application.yml`:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/stock_db
    username: stock_user
    password: your_password

jwt:
  secret: YourVerySecureJWTSecretKeyHere
  expiration: 86400000  # 24 hours in ms
```

### Build & Run

```bash
# Build
mvn clean package

# Run
mvn spring-boot:run

# Or with Docker
docker build -t stock-user-service .
docker run -p 8081:8081 \
  -e DATABASE_URL=jdbc:postgresql://postgres:5432/stock_db \
  -e DATABASE_USER=stock_user \
  -e DATABASE_PASSWORD=password \
  stock-user-service
```

## Testing

```bash
# Run all tests
mvn test

# Run specific test
mvn test -Dtest=UserServiceTest

# Coverage
mvn test jacoco:report
```

## Database Schema

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    risk_profile VARCHAR(20),
    country VARCHAR(100),
    preferred_currency VARCHAR(3),
    investment_experience VARCHAR(20),
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Security

- **Password Hashing**: BCrypt (cost factor: 10)
- **JWT Signing**: HMAC SHA-512
- **Token Expiry**: 24 hours (configurable)
- **CORS**: Configured in API Gateway
- **HTTPS**: Required in production

## Error Handling

| Status | Error | Cause |
|--------|-------|-------|
| 201 | Created | Successful registration |
| 200 | OK | Successful login/request |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Invalid credentials/token |
| 404 | Not Found | User not found |
| 409 | Conflict | Email already registered |
| 500 | Internal Error | Server error |

## Architecture

```
┌─────────────┐
│ AuthController
└──────┬──────┘
       │
┌──────▼──────────┐
│ UserService     │
└──────┬──────────┘
       │
┌──────┬────────────┬──────────┐
│      │            │          │
▼      ▼            ▼          ▼
JWT  Security  Repository  Password
Utils Config   Access     Encoder
```

## Future Enhancements

- [ ] Email verification (OTP)
- [ ] Social login (Google, GitHub)
- [ ] Two-factor authentication
- [ ] Session management
- [ ] Token refresh mechanism
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT
