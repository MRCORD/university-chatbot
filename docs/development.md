# Development Guide

This guide provides comprehensive instructions for setting up and developing the University Chatbot project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Architecture Overview](#architecture-overview)
- [API Development](#api-development)
- [Debugging](#debugging)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Docker & Docker Compose** (optional, for containerized development)
- **Node.js 18+** (if working with frontend components)

### System Dependencies

**macOS:**
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python@3.11 git
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git build-essential curl
```

## Project Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd university-chatbot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv unibot

# Activate virtual environment
# On macOS/Linux:
source unibot/bin/activate

# On Windows:
# unibot\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list
```

## Environment Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your specific configuration:

```bash
# Application Settings
APP_NAME="University Chatbot"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT="development"
LOG_LEVEL="DEBUG"
SECRET_KEY="your-super-secret-key-here"

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

# Supabase Configuration
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Storage Configuration
DOCUMENTS_BUCKET="official-documents"

# AI Provider Settings
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-anthropic-api-key"

# Vector Database
VECTOR_DIMENSION=1536
SIMILARITY_THRESHOLD=0.7

# Redis (if using)
REDIS_URL="redis://localhost:6379"
```

### 3. Supabase Setup

1. Create a new project at [Supabase](https://supabase.com)
2. Copy your project URL and API keys
3. Set up the database schema by running the setup script

## Database Setup

### 1. Initialize Database Schema

```bash
python scripts/setup_database.py
```

This script will:
- Create necessary tables
- Set up Row Level Security (RLS) policies
- Create storage buckets
- Initialize vector extensions

### 2. Create Admin User (Optional)

```bash
python scripts/create_admin_user.py
```

### 3. Ingest Sample Documents

```bash
# Add sample documents to data/sample_documents/
python scripts/ingest_documents.py
```

## Development Workflow

### 1. Start Development Server

```bash
# Standard development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With hot reload and debug logging
uvicorn app.main:app --reload --log-level debug
```

### 2. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 3. Docker Development (Alternative)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Code Quality

### 1. Code Formatting

```bash
# Format code with Black
black app/ tests/ scripts/

# Sort imports with isort
isort app/ tests/ scripts/

# Combine both
black app/ tests/ scripts/ && isort app/ tests/ scripts/
```

### 2. Linting

```bash
# Run flake8 linter
flake8 app/ tests/ scripts/

# Run mypy type checker
mypy app/
```

### 3. Pre-commit Setup (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

## Testing

### 1. Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services/test_conversation_service.py

# Run with verbose output
pytest -v
```

### 2. Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests only
pytest tests/e2e/

# Run tests with specific markers
pytest -m "slow"
pytest -m "not slow"
```

### 3. Test Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# View coverage report
open htmlcov/index.html  # macOS
# Or navigate to htmlcov/index.html in your browser
```

## Architecture Overview

### Project Structure

```
app/
├── api/                    # FastAPI routes and endpoints
│   └── v1/                # API version 1
├── core/                  # Core application configuration
├── engines/               # Conversation engines (LangGraph)
├── interfaces/            # Abstract interfaces and protocols
├── models/                # Pydantic models and schemas
├── providers/             # External service providers
│   ├── database/         # Database providers (Supabase)
│   ├── llm/              # LLM providers (OpenAI, Anthropic)
│   └── storage/          # Storage providers
├── repositories/          # Data access layer
├── services/             # Business logic layer
└── utils/                # Utility functions
```

### Key Design Principles

1. **Clean Architecture**: Separation of concerns with clear boundaries
2. **Dependency Injection**: Using the container pattern for loose coupling
3. **Interface Segregation**: Abstract interfaces for testability
4. **Single Responsibility**: Each module has a single, well-defined purpose

### Data Flow

```
API Endpoint → Service → Repository → Provider → External Service
     ↓           ↓           ↓           ↓
  Validation  Business   Data Access  Integration
             Logic
```

## API Development

### 1. Adding New Endpoints

Create new endpoints in `app/api/v1/`:

```python
# app/api/v1/new_endpoint.py
from fastapi import APIRouter, Depends
from app.core.dependencies import get_service_container
from app.models.requests import NewRequest
from app.models.responses import NewResponse

router = APIRouter(prefix="/new", tags=["new"])

@router.post("/", response_model=NewResponse)
async def create_new_item(
    request: NewRequest,
    container = Depends(get_service_container)
):
    service = container.resolve("new_service")
    return await service.create_item(request)
```

### 2. Request/Response Models

Define models in `app/models/`:

```python
# app/models/new_model.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NewRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class NewResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
```

### 3. Business Logic

Implement services in `app/services/`:

```python
# app/services/new_service.py
from app.interfaces.new_interface import NewServiceInterface
from app.repositories.new_repository import NewRepository

class NewService(NewServiceInterface):
    def __init__(self, repository: NewRepository):
        self.repository = repository
    
    async def create_item(self, request: NewRequest) -> NewResponse:
        # Business logic here
        item = await self.repository.create(request)
        return NewResponse.from_orm(item)
```

## Debugging

### 1. Debug Configuration

VS Code `launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/app/main.py",
            "console": "integratedTerminal",
            "args": ["--reload", "--host", "0.0.0.0", "--port", "8000"],
            "env": {
                "DEBUG": "true"
            }
        }
    ]
}
```

### 2. Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Use structured logging
logger.info("Processing request", user_id=user_id, action="create")
logger.error("Database error", error=str(e), query=query)
```

### 3. Debug Tools

```bash
# Interactive debugging with ipdb
pip install ipdb

# Add breakpoint in code
import ipdb; ipdb.set_trace()

# Debug with pytest
pytest --pdb  # Drop into debugger on failure
pytest --pdb-trace  # Drop into debugger at start of each test
```

## Performance Optimization

### 1. Database Optimization

```python
# Use connection pooling
# Configure in app/providers/database/supabase_provider.py

# Optimize queries
# Use select() with specific columns
# Add proper indexes
# Use pagination for large result sets
```

### 2. Caching

```python
# Redis caching example
from functools import lru_cache
import redis

# In-memory caching
@lru_cache(maxsize=128)
def expensive_operation(param: str) -> str:
    # Expensive computation
    return result

# Redis caching
redis_client = redis.Redis.from_url(settings.REDIS_URL)
```

### 3. Async Best Practices

```python
# Use async/await properly
async def process_documents(documents: List[Document]):
    # Process concurrently
    tasks = [process_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure you're in the project root and venv is activated
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or run with python -m
python -m app.main
```

#### 2. Database Connection Issues

**Problem**: Cannot connect to Supabase

**Solution**:
- Verify environment variables in `.env`
- Check network connectivity
- Ensure Supabase project is active
- Verify API keys are correct

#### 3. Vector Search Issues

**Problem**: Vector similarity search not working

**Solution**:
```bash
# Regenerate embeddings
python scripts/generate_embeddings.py

# Check vector dimensions match
# Verify similarity threshold settings
```

#### 4. Memory Issues

**Problem**: High memory usage during document processing

**Solution**:
- Process documents in batches
- Use streaming for large files
- Implement proper cleanup

#### 5. Performance Issues

**Problem**: Slow API responses

**Solution**:
- Enable database query logging
- Profile slow endpoints
- Implement caching
- Optimize database queries

### Debug Commands

```bash
# Check application health
curl http://localhost:8000/health

# Test API endpoints
python scripts/test_api.py

# Monitor logs
tail -f logs/app.log

# Check database connections
python -c "from app.providers.database.supabase_provider import SupabaseProvider; print(SupabaseProvider().test_connection())"

# Validate environment
python -c "from app.core.config import get_settings; print(get_settings())"
```

### Getting Help

1. **Check the logs**: Most issues are logged with context
2. **Review test failures**: Tests often reveal configuration issues
3. **Verify environment**: Ensure all required variables are set
4. **Check dependencies**: Ensure all packages are installed correctly
5. **Database state**: Verify database schema and data integrity

---

## Next Steps

Once you have the development environment set up:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run the tests**: Execute `pytest` to ensure everything works
3. **Review the architecture**: Understand the codebase structure
4. **Make your first change**: Try adding a simple endpoint
5. **Check deployment docs**: Review `docs/deployment.md` for production setup

For questions or issues, please check the existing issues in the repository or create a new one with detailed information about your problem.