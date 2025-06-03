# University Chatbot API Documentation

## Overview

The University Chatbot API is a RESTful API that provides AI-powered assistance for Universidad del Pacífico students and staff. The API enables natural language conversations, document search, user management, and complaint handling.

**Base URL:** `http://localhost:8000` (development)  
**API Version:** v1  
**API Prefix:** `/api/v1`

## Authentication

Currently, the API uses user ID-based authentication. JWT token authentication is configured but not fully implemented. For now, pass `user_id` in request bodies where required.

## Rate Limiting

Rate limiting is not currently implemented but is planned for production deployment.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
- `501` - Not Implemented

## Endpoints

### Health Check

#### GET /health
Check API health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Chat Endpoints

### POST /api/v1/chat/
Process a chat message and get AI response.

**Request Body:**
```json
{
  "message": "What are the graduation requirements?",
  "conversation_id": "optional-conversation-id",
  "user_id": "user-123",
  "conversation_type": "document_qa",
  "context": {}
}
```

**Parameters:**
- `message` (string, required): User message (1-2000 characters)
- `conversation_id` (string, optional): Existing conversation ID
- `user_id` (string, required): User identifier
- `conversation_type` (string, optional): One of `document_qa`, `complaint_submission`, `procedure_help`, `general`
- `context` (object, optional): Additional context data

**Response:**
```json
{
  "conversation_id": "conv-123",
  "message": {
    "id": "msg-456",
    "role": "assistant",
    "content": "The graduation requirements include...",
    "message_type": "text",
    "metadata": {},
    "created_at": "2025-06-03T10:30:00Z"
  },
  "sources": ["document-1", "document-2"],
  "confidence_score": 0.85,
  "suggested_actions": ["Ask about specific requirements", "View academic calendar"]
}
```

### GET /api/v1/chat/conversations
Get user's conversation history.

**Query Parameters:**
- `user_id` (string, required): User identifier
- `limit` (integer, optional): Maximum number of conversations (default: 20)

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv-123",
      "title": "Graduation Requirements",
      "conversation_type": "document_qa",
      "status": "active",
      "engine_used": "langgraph",
      "messages": [],
      "metadata": {},
      "created_at": "2025-06-03T10:00:00Z",
      "updated_at": "2025-06-03T10:30:00Z"
    }
  ]
}
```

### GET /api/v1/chat/conversations/{conversation_id}
Get specific conversation with messages.

**Path Parameters:**
- `conversation_id` (string, required): Conversation identifier

**Response:**
```json
{
  "id": "conv-123",
  "title": "Graduation Requirements",
  "conversation_type": "document_qa",
  "status": "active",
  "engine_used": "langgraph",
  "messages": [
    {
      "id": "msg-456",
      "role": "user",
      "content": "What are the graduation requirements?",
      "message_type": "text",
      "metadata": {},
      "created_at": "2025-06-03T10:30:00Z"
    }
  ],
  "metadata": {},
  "created_at": "2025-06-03T10:00:00Z",
  "updated_at": "2025-06-03T10:30:00Z"
}
```

---

## Document Endpoints

### POST /api/v1/documents/upload
Upload a new document for processing.

**Request:** Multipart form data
- `file` (file, required): PDF file to upload
- `document_type` (string, required): One of `academic_regulations`, `procedures`, `deadlines_calendar`, `administrative_rules`, `faculty_specific`, `general_information`
- `faculty` (string, optional): Faculty name
- `academic_year` (string, optional): Academic year
- `uploaded_by` (string, required): User who uploaded the document

**Response:**
```json
{
  "id": "doc-123",
  "filename": "graduation_requirements.pdf",
  "original_filename": "graduation_requirements.pdf",
  "document_type": "academic_regulations",
  "storage_url": "https://storage.url/documents/...",
  "file_size_bytes": 1024000,
  "faculty": "Engineering",
  "academic_year": "2025",
  "processing_status": "completed",
  "metadata": {},
  "uploaded_at": "2025-06-03T10:00:00Z"
}
```

### POST /api/v1/documents/search
Search documents using vector similarity.

**Request Body:**
```json
{
  "query": "graduation requirements",
  "document_type": "academic_regulations",
  "faculty": "Engineering",
  "limit": 10,
  "similarity_threshold": 0.7
}
```

**Parameters:**
- `query` (string, required): Search query (1-500 characters)
- `document_type` (string, optional): Filter by document type
- `faculty` (string, optional): Filter by faculty
- `limit` (integer, optional): Maximum results (1-50, default: 10)
- `similarity_threshold` (float, optional): Minimum similarity score (0.0-1.0, default: 0.7)

**Response:**
```json
{
  "query": "graduation requirements",
  "chunks": [
    {
      "id": "chunk-123",
      "content": "To graduate, students must complete...",
      "page_number": 5,
      "section_title": "Graduation Requirements",
      "similarity_score": 0.92,
      "document": {
        "id": "doc-123",
        "filename": "graduation_requirements.pdf",
        "document_type": "academic_regulations",
        "faculty": "Engineering"
      }
    }
  ],
  "total_found": 1
}
```

### GET /api/v1/documents/{document_id}
Get document by ID.

**Status:** Not implemented (501)

---

## User Endpoints

### POST /api/v1/users/
Create a new user.

**Request Body:**
```json
{
  "email": "student@up.edu.pe",
  "student_id": "20231234",
  "faculty": "Engineering",
  "year_of_study": 3,
  "user_type": "student",
  "preferences": {
    "language": "es",
    "notifications": true
  }
}
```

**Parameters:**
- `email` (string, required): Valid email address
- `student_id` (string, optional): Student ID number
- `faculty` (string, optional): Faculty name
- `year_of_study` (integer, optional): Year of study (1-7)
- `user_type` (string, optional): One of `student`, `admin`, `staff`, `guest` (default: `student`)
- `preferences` (object, optional): User preferences

**Response:**
```json
{
  "id": "user-123",
  "email": "student@up.edu.pe",
  "student_id": "20231234",
  "faculty": "Engineering",
  "year_of_study": 3,
  "user_type": "student",
  "preferences": {
    "language": "es",
    "notifications": true
  },
  "is_active": true,
  "created_at": "2025-06-03T10:00:00Z"
}
```

### GET /api/v1/users/{user_id}
Get user by ID.

**Path Parameters:**
- `user_id` (string, required): User identifier

**Response:** Same as create user response

### PUT /api/v1/users/{user_id}
Update user information.

**Status:** Not implemented (501)

---

## Complaint Endpoints

### POST /api/v1/complaints/
Submit a new complaint.

**Request Body:**
```json
{
  "title": "Internet connection issues in library",
  "description": "The WiFi connection is very slow and frequently disconnects...",
  "category": "technology",
  "is_anonymous": false,
  "user_id": "user-123",
  "conversation_id": "conv-456"
}
```

**Parameters:**
- `title` (string, required): Complaint title (5-200 characters)
- `description` (string, required): Detailed description (10-2000 characters)
- `category` (string, required): One of `administrative`, `academic`, `infrastructure`, `technology`, `services`, `financial`, `other`
- `is_anonymous` (boolean, optional): Whether complaint is anonymous (default: false)
- `user_id` (string, optional): Required if not anonymous
- `conversation_id` (string, optional): Associated conversation ID

**Response:**
```json
{
  "id": "complaint-123",
  "title": "Internet connection issues in library",
  "description": "The WiFi connection is very slow...",
  "category": "technology",
  "priority": "medium",
  "status": "submitted",
  "urgency_level": "normal",
  "affected_service": "WiFi",
  "suggested_department": "IT Services",
  "ai_generated_tags": ["wifi", "library", "connectivity"],
  "upvotes": 0,
  "view_count": 0,
  "is_anonymous": false,
  "similar_complaint_ids": [],
  "resolved_at": null,
  "created_at": "2025-06-03T10:00:00Z"
}
```

### GET /api/v1/complaints/
Get public complaints for dashboard.

**Query Parameters:**
- `limit` (integer, optional): Maximum results (1-100, default: 50)
- `category` (string, optional): Filter by category

**Response:**
```json
{
  "complaints": [
    {
      "id": "complaint-123",
      "title": "Internet connection issues in library",
      "category": "technology",
      "priority": "medium",
      "status": "submitted",
      "upvotes": 5,
      "view_count": 25,
      "created_at": "2025-06-03T10:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/complaints/{complaint_id}
Get specific complaint by ID.

**Status:** Not implemented (501)

### POST /api/v1/complaints/{complaint_id}/upvote
Upvote a complaint.

**Status:** Not implemented (501)

---

## Data Models

### Enums

**ConversationType:**
- `document_qa` - Document question & answer
- `complaint_submission` - Complaint submission
- `procedure_help` - Procedure assistance
- `general` - General conversation

**DocumentType:**
- `academic_regulations` - Academic regulations
- `procedures` - Administrative procedures
- `deadlines_calendar` - Deadlines and calendar
- `administrative_rules` - Administrative rules
- `faculty_specific` - Faculty-specific documents
- `general_information` - General information

**ComplaintCategory:**
- `administrative` - Administrative issues
- `academic` - Academic issues
- `infrastructure` - Infrastructure problems
- `technology` - Technology issues
- `services` - Service complaints
- `financial` - Financial issues
- `other` - Other categories

**UserType:**
- `student` - Student user
- `admin` - Administrator
- `staff` - Staff member
- `guest` - Guest user

---

## Configuration

The API uses environment variables for configuration:

### Application Settings
- `APP_NAME`: Application name
- `APP_VERSION`: Version string
- `DEBUG`: Debug mode (true/false)
- `ENVIRONMENT`: Environment name
- `LOG_LEVEL`: Logging level
- `SECRET_KEY`: JWT secret key

### AI Configuration
- `OPENAI_API_KEY`: OpenAI API key
- `CONVERSATION_ENGINE`: Active engine (default: "langgraph")
- `LANGGRAPH_LLM_PROVIDER`: LLM provider (default: "openai")
- `LANGGRAPH_MODEL`: Model name (default: "gpt-4o-mini")
- `EMBEDDING_MODEL`: Embedding model (default: "text-embedding-ada-002")

### Database & Storage
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key

---

## Development

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env

# Run the server
python app/main.py
```

### Interactive Documentation

When running in debug mode, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### CORS Configuration

The API allows cross-origin requests from:
- `http://localhost:3000` (React development server)
- `http://localhost:8000` (API server)

Additional origins can be configured via the `ALLOWED_ORIGINS` environment variable.

---

## Monitoring

The API includes:
- Structured logging with JSON output
- Request timing headers (`X-Process-Time`)
- Health check endpoint
- Optional Sentry integration for error tracking

---

## Notes

- Some endpoints are marked as "Not implemented" (501 status) and are planned for future releases
- The API is designed for Universidad del Pacífico but can be adapted for other institutions
- Vector search functionality requires proper embedding model configuration
- Document processing is handled asynchronously after upload
