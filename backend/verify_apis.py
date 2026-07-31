import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from supabase import create_client

# Reconfigure stdout to support UTF-8 emojis on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Try loading from local and root directories
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

print("=== SDE Prep Portal API Verification ===")

# 1. Check Env Keys
gemini_key = os.getenv("GEMINI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"GEMINI_API_KEY detected: {'YES (starts with ' + gemini_key[:5] + '...)' if gemini_key else 'NO'}")
print(f"SUPABASE_URL detected: {'YES (' + supabase_url + ')' if supabase_url else 'NO'}")
print(f"SUPABASE_KEY detected: {'YES (starts with ' + supabase_key[:5] + '...)' if supabase_key else 'NO'}")

if not gemini_key or not supabase_url or not supabase_key:
    print("❌ Error: Missing credentials. Please populate your keys in .env.")
    sys.exit(1)

# Define structured schema matching streamlit_app.py
class EvaluationResult(BaseModel):
    score: int = Field(..., description="An integer score from 0 to 100.")
    functional_correctness_feedback: str = Field(..., description="Critique on correctness.")
    efficiency_feedback: str = Field(..., description="Critique on efficiency.")
    cleanliness_feedback: str = Field(..., description="Critique on cleanliness.")
    rigor_feedback: str = Field(..., description="Critique on theoretical understanding.")
    socratic_hint: str = Field(..., description="Socratic hint if score < 85.")
    refactored_code: str = Field(..., description="Refactored code if score >= 85.")
    passed: bool = Field(..., description="True if score >= 85.")

# 2. Test Gemini API Call
print("\n--- Testing Google Gemini API (gemini-2.5-flash) ---")
try:
    client = genai.Client(api_key=gemini_key)
    
    test_prompt = """
    Target Challenge: JVM Memory & Reference Simulator
    Target Day: day_1
    STUDENT'S SUBMITTED CODE:
    def solve():
        return True
    STUDENT'S THEORETICAL ANALYSIS / PROOF:
    Java passes by value. Complexity is O(N).
    """
    
    system_instruction = "Act as a strict Senior Tech Lead. Evaluate the code and return a structured JSON response."
    
    print("Calling Gemini API...")
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=test_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=EvaluationResult,
            temperature=0.1
        )
    )
    
    import json
    res_json = json.loads(response.text)
    print("✅ Gemini API Success! Structured output parsed correctly.")
    print(f"Parsed Score: {res_json.get('score')}")
    print(f"Passed status: {res_json.get('passed')}")
    print(f"Socratic Hint snippet: {res_json.get('socratic_hint')[:60] if res_json.get('socratic_hint') else 'None'}")
    
except Exception as e:
    print(f"❌ Gemini API Call failed: {e}")
    sys.exit(1)

# 3. Test Supabase Integration
print("\n--- Testing Supabase DB Connection ---")
try:
    print("Connecting to Supabase client...")
    supabase_client = create_client(supabase_url, supabase_key)
    
    db_data = {
        "user_id": "api_test_user",
        "day_id": "day_1",
        "completed": False,
        "score": 45,
        "code_submission": "def solve(): return True",
        "feedback": "Gemini verification testing status check."
    }
    
    print("Attempting to UPSERT test record into 'sde_portal_progress' table...")
    upsert_res = supabase_client.table("sde_portal_progress").upsert(db_data).execute()
    print("✅ Supabase UPSERT Success!")
    
    print("Attempting to SELECT test record...")
    select_res = supabase_client.table("sde_portal_progress").select("*").eq("user_id", "api_test_user").execute()
    print("✅ Supabase SELECT Success!")
    print(f"Retrieved user: {select_res.data[0]['user_id']} | Score: {select_res.data[0]['score']}")
    
    # Clean up test record
    print("Cleaning up test record...")
    supabase_client.table("sde_portal_progress").delete().eq("user_id", "api_test_user").execute()
    print("✅ Cleanup complete.")
    
except Exception as e:
    print(f"❌ Supabase database interaction failed: {e}")
    print("Please verify that your database schema matches the 'sde_portal_progress' table name and fields.")
    sys.exit(1)

print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! Both Gemini API and Supabase database endpoints are fully functional.")
