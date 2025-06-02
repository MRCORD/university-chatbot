# University Chatbot

AI-powered chatbot for Universidad del Pacífico administrative assistance.

## Features

- 🤖 **Intelligent Document QA** - Query official university documents
- 📋 **Complaint Processing** - Structured complaint collection and public display
- 🔍 **Vector Search** - Semantic similarity search across documents
- ⚡ **Real-time Updates** - Live complaint tracking and status changes
- 🏗️ **Clean Architecture** - Modular, testable, and maintainable code

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repo-url>
   cd university-chatbot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

Environment Configuration
bashcp .env.example .env
# Edit .env with your Supabase and AI provider credentials

Database Setup
bashpython scripts/setup_database.py

Run Development Server
bashuvicorn app.main:app --reload

Access API

API: http://localhost:8000
Docs: http://localhost:8000/docs
Health: http://localhost:8000/health



Project Structure

app/api/ - FastAPI endpoints and routing
app/services/ - Business logic and orchestration
app/repositories/ - Data access layer
app/engines/ - Conversation engines (LangGraph, etc.)
app/providers/ - External service integrations
tests/ - Comprehensive test suite

Development
bash# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black app/ tests/
isort app/ tests/

# Type checking  
mypy app/
Deployment
See docs/deployment.md for production deployment instructions.

---

## **Next Steps After Creating This Structure**

1. **Create the directories:**
   ```bash
   mkdir -p university-chatbot/app/{api/v1,core,interfaces,models,repositories,services,engines,providers/{llm,database,storage},utils}
   mkdir -p university-chatbot/{tests/{unit,integration,e2e},scripts,data/{uploads,processed,sample_documents},docs}

Create empty __init__.py files:
bashfind university-chatbot -type d -name "app" -o -name "tests" | xargs -I {} find {} -type d -exec touch {}/__init__.py \;

Copy the requirements.txt and .env.example files
Start with core configuration (next step)