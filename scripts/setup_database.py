# =======================
# scripts/setup_database.py
# =======================
"""
Script to set up the database schema and initial data.
Run this after creating your Supabase project.
"""
import asyncio
import os
from pathlib import Path

from app.core.config import get_settings
from app.providers.database.supabase_provider import SupabaseProvider

async def setup_database():
    """Set up database with initial data."""
    print("🚀 Setting up University Chatbot database...")
    
    settings = get_settings()
    db = SupabaseProvider(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        # Test database connection
        print("📡 Testing database connection...")
        health = await db.health_check()
        if not health:
            print("❌ Database connection failed!")
            return
        print("✅ Database connection successful!")
        
        # Create admin user
        print("👤 Creating admin user...")
        admin_data = {
            'email': 'admin@up.edu.pe',
            'user_type': 'admin',
            'preferences': {'role': 'system_administrator'},
            'is_active': True
        }
        
        try:
            admin_user = await db.create('users', admin_data)
            print(f"✅ Admin user created with ID: {admin_user['id']}")
        except Exception as e:
            if "duplicate key" in str(e).lower():
                print("ℹ️ Admin user already exists")
            else:
                print(f"⚠️ Failed to create admin user: {e}")
        
        # Create sample documents
        print("📄 Creating sample document records...")
        sample_docs = [
            {
                'filename': 'reglamento_academico_2024.pdf',
                'original_filename': 'Reglamento Académico 2024.pdf',
                'document_type': 'academic_regulations',
                'storage_bucket': 'official-documents',
                'storage_path': 'documents/academic_regulations/reglamento_academico_2024.pdf',
                'processing_status': 'pending',
                'uploaded_by': admin_user['id'] if 'admin_user' in locals() else None
            },
            {
                'filename': 'procedimientos_matricula.pdf',
                'original_filename': 'Procedimientos de Matrícula.pdf',
                'document_type': 'procedures',
                'storage_bucket': 'official-documents',
                'storage_path': 'documents/procedures/procedimientos_matricula.pdf',
                'processing_status': 'pending',
                'uploaded_by': admin_user['id'] if 'admin_user' in locals() else None
            }
        ]
        
        for doc_data in sample_docs:
            try:
                doc = await db.create('documents', doc_data)
                print(f"✅ Sample document created: {doc['filename']}")
            except Exception as e:
                print(f"⚠️ Failed to create document {doc_data['filename']}: {e}")
        
        print("🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Upload some PDF documents using the API")
        print("2. Start the FastAPI server: uvicorn app.main:app --reload")
        print("3. Test the chat endpoint at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(setup_database())

