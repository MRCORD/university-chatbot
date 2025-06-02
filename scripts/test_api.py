# =======================
# scripts/test_api.py
# =======================
"""
Script to test the API endpoints.
"""
import asyncio
import httpx

async def test_api():
    """Test basic API functionality."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing University Chatbot API...")
        
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test chat endpoint
        print("\n2. Testing chat endpoint...")
        try:
            chat_request = {
                "message": "Hello, I need help with enrollment procedures",
                "user_id": "test-user-123"
            }
            
            response = await client.post(f"{base_url}/api/v1/chat/", json=chat_request)
            if response.status_code == 200:
                print("✅ Chat endpoint working")
                chat_response = response.json()
                print(f"   Response: {chat_response['message']['content'][:100]}...")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ Chat endpoint error: {e}")
        
        # Test complaints endpoint
        print("\n3. Testing complaints endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/complaints/")
            if response.status_code == 200:
                print("✅ Complaints endpoint working")
                complaints = response.json()
                print(f"   Found {len(complaints['complaints'])} complaints")
            else:
                print(f"❌ Complaints endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Complaints endpoint error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())

