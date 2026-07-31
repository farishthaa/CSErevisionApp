import streamlit as st
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from supabase import create_client, Client
import streamlit.components.v1 as components

# Load environment variables from current working directory and relative script folder
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Page Config ---
st.set_page_config(
    page_title="SDE Revision Portal - AI Evaluator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sleek Dark Styling ---
st.markdown(
    """
    <style>
    /* Dark Theme Core CSS */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Input field styling (targeting wrappers and inner controls) */
    div[data-baseweb="textarea"], 
    div[data-baseweb="input"],
    div[data-baseweb="textarea"] textarea, 
    div[data-baseweb="input"] input,
    textarea, 
    input {
        background-color: #1e293b !important;
        color: #f3f4f6 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="textarea"], div[data-baseweb="input"] {
        border: 1px solid #334155 !important;
    }
    textarea {
        font-family: 'Courier New', Courier, monospace !important;
    }
    
    /* Header/Text elements */
    h1, h2, h3, p, label {
        color: #f3f4f6 !important;
    }
    
    /* Reset alert and notification text to inherit theme colors for readability */
    div[role="alert"], 
    div[role="alert"] *, 
    div[data-testid="stNotification"], 
    div[data-testid="stNotification"] *, 
    .stAlert, 
    .stAlert * {
        color: inherit !important;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }
    
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
    }
    
    /* Feedback card blocks */
    .feedback-card {
        background-color: #111827;
        border-left: 4px solid #4f46e5;
        padding: 1.2rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .feedback-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #818cf8;
        margin-bottom: 0.5rem;
    }
    .feedback-score {
        float: right;
        font-size: 0.9rem;
        background: #312e81;
        padding: 2px 8px;
        border-radius: 12px;
        color: #c7d2fe;
    }
    
    /* Socratic Hint Styling */
    .socratic-hint {
        background-color: #1e1b4b;
        border: 1px solid #4338ca;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .socratic-title {
        color: #a5b4fc;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Define Evaluation JSON Schema via Pydantic ---
class EvaluationResult(BaseModel):
    score: int = Field(..., description="An integer score from 0 to 100 indicating the total grade.")
    functional_correctness_feedback: str = Field(..., description="Direct feedback on correctness (40%). Identify edge cases.")
    efficiency_feedback: str = Field(..., description="Feedback on space and time complexity, efficiency (30%).")
    cleanliness_feedback: str = Field(..., description="Critique on naming conventions, design patterns, and readability (20%).")
    rigor_feedback: str = Field(..., description="Critique on theoretical understanding of concepts like JVM stack/heap, value reference, Big-O proofs (10%).")
    socratic_hint: str = Field(..., description="Strict Socratic hint pointing out failing edge cases or memory leaks if score < 85. Leave empty if score >= 85. Do NOT give direct code fixes.")
    refactored_code: str = Field(..., description="Production-grade, clean, refactored solution if score >= 85. Leave empty if score < 85.")
    passed: bool = Field(..., description="Set to True if score >= 85, otherwise False.")

# --- Helper functions ---

def load_content():
    """Loads the core 90-day syllabus syllabus from content.json files."""
    paths = [
        "content.json",
        "backend/content.json",
        "../frontend/content.json",
        "frontend/content.json"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                pass
    # Fallback default syllabus for day 1
    return {
        "days": {
            "day_1": {
                "title": "JVM Memory & Big-O Reference Simulation",
                "topics": ["JVM Memory", "Stack & Heap", "Pass-by-Value", "Big-O Analysis"],
                "difficulty": "Medium",
                "coding_challenge": {
                    "title": "Build a Heap & Stack Allocator Simulator",
                    "description": "Implement a class `MemorySimulator` in Python that tracks variables, references, and frames. Define: \n- `push_stack_frame(method_name)`\n- `pop_stack_frame()`\n- `allocate_heap(obj_type, data_dict)` -> returns a memory address\n- `assign_ref(var_name, address)` -> binds local variable to heap address\n- `check_memory_leaks()` -> checks for orphaned heap items\n\nExplain within your code docstrings and theoretical input how Java references are passed by value and prove the Big-O complexities of your allocator functions.",
                    "starter_code": "class MemorySimulator:\n    def __init__(self):\n        self.stack = []  # List of frames: {'method': str, 'locals': dict}\n        self.heap = {}   # Address mapping: {int: {'type': str, 'data': dict, 'ref_count': int}}\n        self.address_counter = 1000\n        \n    def push_stack_frame(self, method_name: str):\n        # TODO: Implement stack frame allocation\n        pass\n        \n    def pop_stack_frame(self):\n        # TODO: Implement frame removal\n        pass\n        \n    def allocate_heap(self, obj_type: str, data: dict) -> int:\n        # TODO: Allocate space in heap and return address\n        return 0\n        \n    def assign_ref(self, var_name: str, address: int):\n        # TODO: Assign local variable to point to heap address\n        pass\n        \n    def check_memory_leaks(pelf) -> list:\n        # TODO: Return list of heap addresses with no active references in stack frames\n        return []"
                }
            }
        }
    }

def get_keys():
    """Retrieve keys from environment variable, streamlit secrets, or session state fallback."""
    gemini_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("GEMINI_API_KEY", "")
    supabase_url = os.getenv("SUPABASE_URL") or st.session_state.get("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY") or st.session_state.get("SUPABASE_KEY", "")
    
    # Try fetching from st.secrets if deployed on Streamlit Cloud
    try:
        if not gemini_key and "GEMINI_API_KEY" in st.secrets:
            gemini_key = st.secrets["GEMINI_API_KEY"]
        if not supabase_url and "SUPABASE_URL" in st.secrets:
            supabase_url = st.secrets["SUPABASE_URL"]
        if not supabase_key and "SUPABASE_KEY" in st.secrets:
            supabase_key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass
        
    return gemini_key, supabase_url, supabase_key

# --- Initialization ---
content_data = load_content()

# Get Day & User IDs from query parameters
query_params = st.query_params
day_id = query_params.get("day_id", "day_1")
user_id = query_params.get("user_id", "candidate_user")

# Read Syllabus Content
day_content = content_data.get("days", {}).get(day_id)
if not day_content:
    # If the day does not have explicit content, construct a default
    day_content = {
        "title": f"Day {day_id.replace('day_', '')} Revision Challenge",
        "topics": ["General SDE Review"],
        "difficulty": "Medium",
        "coding_challenge": {
            "title": f"Topic: Day {day_id.replace('day_', '')} Challenge",
            "description": f"Write an optimal solution demonstrating standard data structure manipulations for {day_id}.",
            "starter_code": "def solve_challenge():\n    # Write your solution here\n    pass"
        }
    }

challenge = day_content.get("coding_challenge", {})

# Retrieve keys
gemini_key, supabase_url, supabase_key = get_keys()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🔑 API Configurations")
    st.caption("Environment variables or secrets will populate these automatically. Otherwise, input them manually below.")
    
    # Gemini Key Form
    form_gemini = st.text_input(
        "Google Gemini API Key",
        value=gemini_key if gemini_key else "",
        type="password",
        help="Required for AI Code Evaluation"
    )
    if form_gemini:
        st.session_state["GEMINI_API_KEY"] = form_gemini
        gemini_key = form_gemini
        
    # Supabase Url Form
    form_supa_url = st.text_input(
        "Supabase URL",
        value=supabase_url if supabase_url else "",
        help="Required for cloud sync"
    )
    if form_supa_url:
        st.session_state["SUPABASE_URL"] = form_supa_url
        supabase_url = form_supa_url
        
    # Supabase Key Form
    form_supa_key = st.text_input(
        "Supabase Anon Key",
        value=supabase_key if supabase_key else "",
        type="password",
        help="Required for cloud sync"
    )
    if form_supa_key:
        st.session_state["SUPABASE_KEY"] = form_supa_key
        supabase_key = form_supa_key
        
    st.divider()
    st.subheader("📋 Session Info")
    st.write(f"**Day:** `{day_id.upper()}`")
    st.write(f"**User ID:** `{user_id}`")
    
    # Status badges
    if gemini_key:
        st.success("✅ Gemini Connected")
    else:
        st.warning("⚠️ Gemini Key Missing")
        
    if supabase_url and supabase_key:
        st.success("✅ Supabase Connected")
    else:
        st.info("ℹ️ Running in Local-Only Mode")

# Initialize Client Variables
supabase_client = None
if supabase_url and supabase_key:
    try:
        supabase_client = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.sidebar.error(f"Supabase Client Connection Error: {e}")

# --- Main Layout ---
st.title("🤖 SDE Practice & AI Evaluator")
st.write(f"**Focus:** {', '.join(day_content.get('topics', []))} | **Difficulty:** `{day_content.get('difficulty', 'Medium')}`")

st.divider()

# Left and Right layout columns
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.subheader(f"📝 Coding Challenge: {challenge.get('title', 'Solve Challenge')}")
    st.markdown(challenge.get("description", "No challenge description provided."))
    
    # Code Text Area (custom formatted)
    code_submission = st.text_area(
        "Write your code implementation:",
        value=challenge.get("starter_code", ""),
        height=320,
        key="code_area"
    )

with col2:
    st.subheader("📚 Theoretical Proof & Complexity Analysis")
    st.markdown(
        """
        Explain the space and time complexity in Big-O notation. 
        Prove how references are allocated or passed based on today's concepts.
        """
    )
    theoretical_proof = st.text_area(
        "Write your theoretical analysis here:",
        placeholder="Explain your approach, verify the complexity, and answer any theoretical proof questions...",
        height=280,
        key="proof_area"
    )
    
    submit_btn = st.button("🚀 Submit to Senior Tech Lead")

# --- Action Logic: Evaluation & Sync ---
if submit_btn:
    if not gemini_key:
        st.error("❌ Cannot evaluate. Google Gemini API key is missing. Add it in the sidebar to proceed.")
    else:
        with st.spinner("🕵️ Senior Tech Lead is reviewing your code..."):
            # Initialize Gemini API Client
            client = genai.Client(api_key=gemini_key)
            
            prompt = f"""
            Target Challenge: {challenge.get('title')}
            Target Day: {day_id}
            
            Challenge Context & Description:
            {challenge.get('description')}
            
            Starter Template Provided:
            {challenge.get('starter_code')}
            
            ------------------------------------------
            STUDENT'S SUBMITTED CODE:
            ```python
            {code_submission}
            ```
            
            STUDENT'S THEORETICAL ANALYSIS / PROOF:
            {theoretical_proof}
            ------------------------------------------
            """
            
            system_instruction = (
                "Act as a strict Senior Tech Lead. Evaluate the student's submission for:\n"
                "1. Functional Correctness (40% weight)\n"
                "2. Efficiency & Complexity (30% weight) - Must evaluate Big-O proofs\n"
                "3. Code Cleanliness (20% weight) - Check PEP8, naming conventions, docstrings\n"
                "4. Theoretical Rigor (10% weight) - Look for solid conceptual explanations\n\n"
                "Provide a total integer score out of 100. Be strict!\n\n"
                "GRADUATED RESPONSE RULES:\n"
                "- If the Score is LESS THAN 85%:\n"
                "  - State that they failed to meet requirements (< 85%).\n"
                "  - You MUST construct a Socratic Hint (`socratic_hint`) that points out the failing edge case, logic bug, complexity bottleneck, or memory leak.\n"
                "  - DO NOT give the direct refactored code or direct fix. The field `refactored_code` MUST remain empty.\n"
                "  - Set `passed = false`.\n"
                "- If the Score is 85% OR GREATER:\n"
                "  - Praise their excellent engineering standard.\n"
                "  - You MUST write the production-grade, optimal, and comments-documented refactored solution inside the `refactored_code` field.\n"
                "  - Include the token '[PASSED]' inside your feedback summaries.\n"
                "  - Set `passed = true`."
            )
            
            try:
                # Call Gemini API with structured outputs
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=EvaluationResult,
                        temperature=0.1,
                    )
                )
                
                # Parse structured JSON output
                res_data = json.loads(response.text)
                
                st.session_state["eval_result"] = res_data
                st.success("✅ Code evaluation complete!")
                
            except Exception as e:
                st.error(f"Failed to evaluate submission: {e}")
                st.session_state["eval_result"] = None

# --- Display Results ---
if "eval_result" in st.session_state and st.session_state["eval_result"]:
    result = st.session_state["eval_result"]
    score = result.get("score", 0)
    passed = result.get("passed", False)
    
    st.divider()
    st.subheader("📊 Evaluation Report")
    
    # Renders score metrics
    m1, m2 = st.columns([1, 4])
    with m1:
        if passed:
            st.metric(label="Status", value="PASSED 🎉")
        else:
            st.metric(label="Status", value="REDO 🔄")
    with m2:
        st.metric(label="Total Score Evaluated", value=f"{score} / 100")
        
    # Detail Breakdown Layout
    tab1, tab2 = st.columns(2, gap="medium")
    
    with tab1:
        st.markdown(
            f"""
            <div class="feedback-card">
                <span class="feedback-score">40% Weight</span>
                <div class="feedback-title">⚙️ Functional Correctness</div>
                <div>{result.get('functional_correctness_feedback', 'No feedback provided.')}</div>
            </div>
            <div class="feedback-card">
                <span class="feedback-score">30% Weight</span>
                <div class="feedback-title">⚡ Efficiency & Complexity</div>
                <div>{result.get('efficiency_feedback', 'No feedback provided.')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with tab2:
        st.markdown(
            f"""
            <div class="feedback-card">
                <span class="feedback-score">20% Weight</span>
                <div class="feedback-title">🎨 Code Cleanliness & Style</div>
                <div>{result.get('cleanliness_feedback', 'No feedback provided.')}</div>
            </div>
            <div class="feedback-card">
                <span class="feedback-score">10% Weight</span>
                <div class="feedback-title">🧠 Theoretical Rigor</div>
                <div>{result.get('rigor_feedback', 'No feedback provided.')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    # Socratic hint or Production-grade Code display
    if not passed:
        st.markdown(
            f"""
            <div class="socratic-hint">
                <div class="socratic-title">💡 Socratic Hint from Senior Tech Lead:</div>
                <div style="font-size: 1.05rem; line-height: 1.6; color: #cbd5e1;">
                    {result.get('socratic_hint', 'Think about edge cases, null arguments, or reference handling.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.balloons()
        st.markdown("### 🏆 Production-Grade Refactored Code:")
        st.code(result.get("refactored_code", "# Correct code verified by Tech Lead"), language="python")
        
    # Sync to Supabase
    db_sync_status = "Skipped (Credentials not set)"
    if supabase_client:
        try:
            db_data = {
                "user_id": user_id,
                "day_id": day_id,
                "completed": passed,
                "score": score,
                "code_submission": code_submission,
                "feedback": result.get("socratic_hint") if not passed else "Passed. " + result.get("functional_correctness_feedback")
            }
            supabase_client.table("sde_portal_progress").upsert(db_data, on_conflict="user_id,day_id").execute()
            db_sync_status = "Synced Successfully ✅"
        except Exception as ex:
            db_sync_status = f"Failed to sync: {ex} ❌"
            
    st.caption(f"**Database Cloud Sync:** {db_sync_status}")
    
    # HTML5 Cross-Origin postMessage triggering
    # This allows the parent window on GitHub Pages to receive and log this state change instantly!
    components.html(
        f"""
        <script>
        (function() {{
            const data = {{
                type: 'SDE_PORTAL_EVALUATION',
                day_id: '{day_id}',
                score: {score},
                completed: {str(passed).lower()},
                feedback: {json.dumps(result.get('socratic_hint') if not passed else 'PASSED! Code refactored.')}
            }};
            console.log("Emitting evaluation postMessage to parent:", data);
            window.parent.postMessage(data, '*');
        }})();
        </script>
        """,
        height=0,
        width=0
    )
