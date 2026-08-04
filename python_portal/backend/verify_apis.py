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

print("=== Python Portal API Verification ===")

# 1. Check Env Keys
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"GEMINI_API_KEY detected: {'YES (starts with ' + gemini_key[:5] + '...)' if gemini_key else 'NO'}")
print(f"OPENAI_API_KEY detected: {'YES (starts with ' + openai_key[:5] + '...)' if openai_key else 'NO'}")
print(f"SUPABASE_URL detected: {'YES (' + supabase_url + ')' if supabase_url else 'NO'}")
print(f"SUPABASE_KEY detected: {'YES (starts with ' + supabase_key[:5] + '...)' if supabase_key else 'NO'}")

if not supabase_url or not supabase_key:
    print("❌ Error: Missing Supabase credentials in .env.")
    sys.exit(1)

if not gemini_key and not openai_key:
    print("❌ Error: Must configure at least one of GEMINI_API_KEY or OPENAI_API_KEY in .env.")
    sys.exit(1)

# Define structured schema matching python portal streamlit app
class EvaluationResult(BaseModel):
    score: int = Field(..., description="An integer score from 0 to 100.")
    functional_correctness_feedback: str = Field(..., description="Critique on code logic.")
    efficiency_feedback: str = Field(..., description="Critique on Pythonic styling (PEP8) and memory complexity.")
    cleanliness_feedback: str = Field(..., description="Critique on spacing, naming, and comments.")
    rigor_feedback: str = Field(..., description="Critique on the student's theoretical explanations.")
    socratic_hint: str = Field(..., description="Socratic tutor hints if score < 85.")
    refactored_code: str = Field(..., description="Optimal code solution if score >= 85.")
    passed: bool = Field(..., description="True if score >= 85.")

# 2. Test Gemini API Call
if gemini_key:
    print("\n--- Testing Google Gemini API (gemini-3.5-flash) ---")
    try:
        client = genai.Client(api_key=gemini_key)
        
        test_prompt = """
        Target Challenge: Python Variables & Math
        Target Day: day_1
        STUDENT'S SUBMITTED CODE:
        def solve(a, b):
            return a + b
        STUDENT'S THEORETICAL ANALYSIS / PROOF:
        Adding two variables takes O(1) time complexity.
        """
        
        system_instruction = "Act as a patient Python Tutor. Evaluate the code and return a structured JSON response."
        
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
        
    except Exception as e:
        print(f"❌ Gemini API Call failed: {e}")
        sys.exit(1)
else:
    print("\nℹ️ Skipping Gemini API check (GEMINI_API_KEY not configured).")

# 3. Test OpenAI API Call
if openai_key:
    print("\n--- Testing OpenAI API (gpt-4o-mini) ---")
    try:
        from openai import OpenAI
        import json
        client = OpenAI(api_key=openai_key)
        
        test_prompt = """
        Target Challenge: Python Variables & Math
        Target Day: day_1
        STUDENT'S SUBMITTED CODE:
        def solve(a, b):
            return a + b
        STUDENT'S THEORETICAL ANALYSIS / PROOF:
        Adding two variables takes O(1) time complexity.
        """
        
        system_instruction = "Act as a patient Python Tutor. Evaluate the code and return a structured JSON response."
        
        print("Calling OpenAI API...")
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": test_prompt}
            ],
            response_format=EvaluationResult,
            temperature=0.1
        )
        
        res_json = json.loads(completion.choices[0].message.content)
        print("✅ OpenAI API Success! Structured output parsed correctly.")
        print(f"Parsed Score: {res_json.get('score')}")
        print(f"Passed status: {res_json.get('passed')}")
        
    except Exception as e:
        print(f"❌ OpenAI API Call failed: {e}")
        sys.exit(1)
else:
    print("\nℹ️ Skipping OpenAI API check (OPENAI_API_KEY not configured).")

# 4. Test Supabase Integration
print("\n--- Testing Supabase DB Connection (python_portal_progress) ---")
try:
    print("Connecting to Supabase client...")
    supabase_client = create_client(supabase_url, supabase_key)
    
    db_data = {
        "user_id": "python_test_user",
        "day_id": "day_1",
        "completed": False,
        "score": 50,
        "code_submission": "def solve(a,b): return a+b",
        "feedback": "Python verification testing status check."
    }
    
    print("Attempting to UPSERT test record into 'python_portal_progress' table...")
    upsert_res = supabase_client.table("python_portal_progress").upsert(db_data, on_conflict="user_id,day_id").execute()
    print("✅ Supabase UPSERT Success!")
    
    print("Attempting to SELECT test record...")
    select_res = supabase_client.table("python_portal_progress").select("*").eq("user_id", "python_test_user").execute()
    print("✅ Supabase SELECT Success!")
    print(f"Retrieved user: {select_res.data[0]['user_id']} | Score: {select_res.data[0]['score']}")
    
    # Clean up test record
    print("Cleaning up test record...")
    supabase_client.table("python_portal_progress").delete().eq("user_id", "python_test_user").execute()
    print("✅ Cleanup complete.")
    
except Exception as e:
    print(f"❌ Supabase database interaction failed: {e}")
    print("Please verify that your database schema matches the 'python_portal_progress' table name and fields.")
    sys.exit(1)

print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! Python Portal backend connects securely to AI services and Supabase.")
