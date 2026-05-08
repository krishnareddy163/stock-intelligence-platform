# Stock Market Intelligence Platform - Contributing Guide

## Code of Conduct

This project adheres to the Contributor Covenant. By participating, you're expected to uphold the standards of respectful communication and collaboration.

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Java 17+
- Python 3.11+
- Git

### Setup Development Environment

```bash
# 1. Clone the repository
git clone <repository-url>
cd claude_mcp_project

# 2. Create development environment
make setup
make dev

# 3. Verify services
docker-compose ps
```

---

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

**Branch Naming Convention:**
- `feature/` — New features
- `bugfix/` — Bug fixes
- `docs/` — Documentation
- `test/` — Tests
- `devops/` — Infrastructure changes

### 2. Make Changes

#### Java Backend
- Follow Spring Boot conventions
- Add unit tests (JUnit 5)
- Update pom.xml if adding dependencies

#### Python MCP Servers
- Use FastAPI patterns
- Add Pydantic models for validation
- Write docstrings
- Add unit tests (pytest)

#### Frontend
- Use functional components (React 18)
- TypeScript for type safety
- CSS Modules or TailwindCSS

### 3. Testing

```bash
# Java tests
cd backend/api-gateway && mvn test

# Python tests
cd mcp-servers/stock-data-server && python -m pytest -v

# Frontend tests
cd frontend && npm test
```

### 4. Code Quality

```bash
# Lint
make lint

# Check formatting
mvn checkstyle:check

# Code coverage
mvn test jacoco:report
```

### 5. Commit & Push

```bash
# Follow commit message convention
git add .
git commit -m "feat: add new stock ranking algorithm"
git push origin feature/your-feature-name
```

**Commit Message Format:**
```
type(scope): description

[optional body]
[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 6. Create Pull Request

- Describe what changed
- Reference related issues
- Ensure CI/CD passes
- Request review from maintainers

---

## Code Standards

### Java
- Use Spring Boot 3.2+ conventions
- Dependency injection via constructor
- Avoid `@Autowired`, use constructor injection
- Write meaningful variable names
- Add JavaDoc for public methods
- Unit test coverage: >80%

### Python
- PEP 8 compliance
- Type hints for all functions
- Docstrings for modules/functions/classes
- Use pytest for testing
- Unit test coverage: >80%

### Frontend
- Functional components preferred
- Props destructuring
- Meaningful component names
- TypeScript strict mode
- CSS Modules or Tailwind

---

## Adding a New MCP Server

1. Create directory: `mcp-servers/your-server-name/`
2. Create:
   - `main.py` — FastAPI app
   - `requirements.txt` — Dependencies
   - `Dockerfile` — Container definition
   - `tests/` — Unit tests
3. Register in `docker-compose.yml`
4. Update `ARCHITECTURE.md`
5. Document tools/endpoints

**Template:**
```python
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Your MCP Server")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/tools/your_tool")
async def your_tool(input_data: YourModel):
    """Your tool description"""
    try:
        # Implementation
        return {"result": "..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Adding a New Microservice

1. Create directory: `backend/your-service/`
2. Create:
   - `pom.xml` — Maven config
   - `src/main/java/com/stock/...` — Source code
   - `src/test/java/...` — Tests
   - `Dockerfile` — Container definition
   - `application.yml` — Configuration
3. Register in `docker-compose.yml`
4. Add health check
5. Update `ARCHITECTURE.md`

---

## Deployment

### Development
```bash
make dev
# Services at localhost:8080, 5001-5005
```

### Production (requires AWS/cloud setup)
```bash
make prod
```

---

## CI/CD Pipeline

The following checks run automatically on push:

1. **Code Quality**
   - SonarQube analysis
   - Checkstyle for Java
   - Flake8 for Python

2. **Tests**
   - Unit tests (Maven, pytest)
   - Integration tests
   - Coverage reports

3. **Build**
   - Docker image build
   - Push to registry

4. **Deploy**
   - Staging environment
   - Production (manual approval)

---

## Documentation

### Update Documentation When
- Adding new features
- Changing API endpoints
- Modifying database schema
- Adding MCP servers

### Documentation Files
- `docs/ARCHITECTURE.md` — System design
- `docs/DATABASE_SCHEMA.md` — Database
- `docs/MCP_DESIGN.md` — MCP servers
- `docs/MVP_ROADMAP.md` — Timeline

---

## Common Tasks

### Adding a Database Migration
```bash
mvn flyway:migrate
# or
liquibase update
```

### Adding a Python dependency
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt
pip install -r requirements.txt
```

### Running specific test
```bash
# Java
mvn test -Dtest=YourTestClass

# Python
pytest tests/test_yourmodule.py -v
```

---

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs -f service-name

# Remove and restart
docker-compose down -v
docker-compose up -d
```

### Database connection error
```bash
# Check PostgreSQL health
docker exec postgres_stock_db pg_isready

# Verify .env file has correct credentials
cat .env
```

### MCP server not responding
```bash
# Check
 service logs
docker logs stock_data_mcp

# Test endpoint
curl http://localhost:5001/health
```

---

## Getting Help

1. Check [`docs/`](docs/) for documentation
2. Search GitHub Issues
3. Create a new issue with:
   - Clear description
   - Steps to reproduce (if bug)
   - Expected vs actual behavior
   - OS and versions

---

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

**Thank you for contributing to the Stock Market Intelligence Platform!** 🚀
