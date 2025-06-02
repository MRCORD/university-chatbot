# =======================
# SETUP INSTRUCTIONS
# =======================

## 🚀 Quick Start Guide

### 1. Clone and Setup Environment

```bash
# Create project directory
mkdir university-chatbot
cd university-chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Create the project structure (copy all the files from the artifacts)
```

### 2. Install Dependencies

```bash
# Create requirements.txt with the content from above
pip install -r requirements.txt
```

### 3. Set Up Supabase

1. **Create Supabase Project:**
   - Go to https://supabase.com
   - Create new project
   - Note your Project URL and API keys

2. **Set Up Database:**
   - Go to SQL Editor in Supabase Dashboard
   - Run the database schema script (from previous artifact)
   - Run the storage buckets script (from previous artifact)

3. **Configure Storage:**
   - Go to Storage in Supabase Dashboard
   - Verify buckets were created: `official-documents`, `user-uploads`, `processed-content`

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values:
# - Add your Supabase URL and keys
# - Add your OpenAI API key
# - Adjust other settings as needed
```

### 5. Initialize Database

```bash
# Run setup script
python scripts/setup_database.py

# Create admin user
python scripts/create_admin_user.py admin@up.edu.pe
```

### 6. Start the Application

```bash
# Start development server
uvicorn app.main:app --reload

# Or use the script
python -m app.main
```

### 7. Test the API

```bash
# Test endpoints
python scripts/test_api.py

# Or visit the interactive docs
# http://localhost:8000/docs
```

## 📋 What You Can Do Now

✅ **Chat with the bot:** POST `/api/v1/chat/`
✅ **Upload documents:** POST `/api/v1/documents/upload`
✅ **Submit complaints:** POST `/api/v1/complaints/`
✅ **View complaints:** GET `/api/v1/complaints/`
✅ **Create users:** POST `/api/v1/users/`

## 🔧 Development Commands

```bash
# Run tests (when implemented)
pytest

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Start with Docker
docker-compose up --build
```