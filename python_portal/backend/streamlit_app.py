import os
import sys
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from supabase import create_client

# Reconfigure stdout to support UTF-8 emojis on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Try loading env variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Page Setup & Styles ---
st.set_page_config(
    page_title="Python Tutor - Evaluator",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom high-contrast Dark theme style overrides
st.markdown("""
<style>
    /* Force dark background matching frontend */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
    }
    
    /* Input field styling */
    div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input {
        background-color: #1e293b !important;
        color: #f3f4f6 !important;
        border: 1px solid #334155 !important;
        font-family: 'Fira Code', monospace !important;
    }
    
    /* Success, warning, error, info text color reset */
    div[role="alert"] * {
        color: inherit !important;
    }
    
    /* Code headers and tags */
    code {
        background-color: #1e293b !important;
        color: #f43f5e !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Schema Definitions ---
class EvaluationResult(BaseModel):
    score: int = Field(..., description="An integer score from 0 to 100 based on solution accuracy.")
    functional_correctness_feedback: str = Field(..., description="Details on functional correctness and edge cases.")
    efficiency_feedback: str = Field(..., description="Critique on Pythonic styling (PEP8) and algorithm complexity.")
    cleanliness_feedback: str = Field(..., description="Critique on variable naming, readability, and comments.")
    rigor_feedback: str = Field(..., description="Feedback on the student's theoretical explanations.")
    socratic_hint: str = Field(..., description="A gentle Socratic question to guide the student if score < 85.")
    refactored_code: str = Field(..., description="The optimal PEP 8 compliant solution if score >= 85.")
    passed: bool = Field(..., description="Set to True if score is 85 or above.")

# --- Loader Functions ---
def load_content():
    """Load python curriculum content.json from current folder, parent folders, or fallback to default."""
    paths = [
        "content.json",
        os.path.join(os.path.dirname(__file__), "content.json"),
        os.path.join(os.path.dirname(__file__), "../frontend/content.json"),
        os.path.join(os.path.dirname(__file__), "../../frontend/content.json")
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {"days": {}}

def get_keys():
    """Retrieve keys from environment variable, streamlit secrets, or session state fallback."""
    gemini_key = os.getenv("GEMINI_API_KEY") or st.session_state.get("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY") or st.session_state.get("OPENAI_API_KEY", "")
    supabase_url = os.getenv("SUPABASE_URL") or st.session_state.get("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY") or st.session_state.get("SUPABASE_KEY", "")
    
    try:
        if not gemini_key and "GEMINI_API_KEY" in st.secrets:
            gemini_key = st.secrets["GEMINI_API_KEY"]
        if not openai_key and "OPENAI_API_KEY" in st.secrets:
            openai_key = st.secrets["OPENAI_API_KEY"]
        if not supabase_url and "SUPABASE_URL" in st.secrets:
            supabase_url = st.secrets["SUPABASE_URL"]
        if not supabase_key and "SUPABASE_KEY" in st.secrets:
            supabase_key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass
        
    return gemini_key, openai_key, supabase_url, supabase_key

# --- Initialization ---
content_data = load_content()

# Retrieve query parameters from dashboard iframe context
query_params = st.query_params
day_id = query_params.get("day_id", "day_1")
user_id = query_params.get("user_id", "candidate_python_user")

# Retrieve metadata for the day's challenge
day_content = content_data.get("days", {}).get(day_id, {})
challenge = day_content.get("coding_challenge", {})
challenge_type = challenge.get("type", "write_code") # write_code, fill_code, troubleshoot

# Retrieve keys
gemini_key, openai_key, supabase_url, supabase_key = get_keys()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🔑 API Configurations")
    st.caption("Environment variables or secrets will populate these automatically. Otherwise, input them manually below.")
    
    # Active LLM Selection
    engine_options = []
    if openai_key:
        engine_options.append("OpenAI (gpt-4o-mini)")
    if gemini_key:
        engine_options.append("Gemini (gemini-3.5-flash)")
    if not engine_options:
        engine_options = ["OpenAI (gpt-4o-mini)", "Gemini (gemini-3.5-flash)"]
        
    active_engine = st.selectbox(
        "Active LLM Engine",
        options=engine_options,
        index=0,
        help="Choose the model used to grade submissions"
    )
    
    # Advanced Overrides Expander
    with st.expander("⚙️ Custom Keys & Overrides (Advanced)"):
        st.caption("Input custom credentials to override the default configurations.")
        
        # OpenAI Key Form
        openai_placeholder = "••••••••••••••••" if openai_key else "Enter your OpenAI key"
        form_openai = st.text_input(
            "OpenAI API Key",
            value="",
            type="password",
            placeholder=openai_placeholder,
            help="Optional: Input a custom key to override the system key."
        )
        if form_openai:
            st.session_state["OPENAI_API_KEY"] = form_openai
            openai_key = form_openai
            
        # Gemini Key Form
        gemini_placeholder = "••••••••••••••••" if gemini_key else "Enter your Gemini key"
        form_gemini = st.text_input(
            "Google Gemini API Key",
            value="",
            type="password",
            placeholder=gemini_placeholder,
            help="Optional: Input a custom key to override the system key."
        )
        if form_gemini:
            st.session_state["GEMINI_API_KEY"] = form_gemini
            gemini_key = form_gemini
            
        # Supabase Url Form
        supa_url_placeholder = "https://your-project.supabase.co"
        if supabase_url:
            parts = supabase_url.split("//")
            if len(parts) > 1:
                domain = parts[1]
                supa_url_placeholder = f"https://{domain[:4]}...{domain[-12:]}"
        
        form_supa_url = st.text_input(
            "Supabase URL",
            value="",
            placeholder=supa_url_placeholder,
            help="Optional: Input custom URL to override configuration."
        )
        if form_supa_url:
            st.session_state["SUPABASE_URL"] = form_supa_url
            supabase_url = form_supa_url
            
        # Supabase Key Form
        supa_key_placeholder = "••••••••••••••••" if supabase_key else "your-anon-key"
        form_supa_key = st.text_input(
            "Supabase Anon Key",
            value="",
            type="password",
            placeholder=supa_key_placeholder,
            help="Optional: Input custom Key to override configuration."
        )
        if form_supa_key:
            st.session_state["SUPABASE_KEY"] = form_supa_key
            supabase_key = form_supa_key
        
    st.divider()
    st.subheader("📋 Session Info")
    st.write(f"**Day:** `{day_id.upper()}`")
    st.write(f"**User ID:** `{user_id}`")
    
    # Status badges
    if "OpenAI" in active_engine:
        if openai_key:
            st.success("✅ OpenAI Connected")
        else:
            st.warning("⚠️ OpenAI Key Missing")
    else:
        if gemini_key:
            st.success("✅ Gemini Connected")
        else:
            st.warning("⚠️ Gemini Key Missing")
        
    if supabase_url and supabase_key:
        st.success("✅ Supabase Connected")
    else:
        st.info("ℹ️ Running in Local-Only Mode")

# --- Main App Frame ---
st.title("🐍 AI Python Tutor Sandbox")
st.subheader(challenge.get("title", "Python Sandbox Challenge"))
st.caption(f"Challenge Format: **{challenge_type.replace('_', ' ').title()}**")

# Challenge Instructions
st.markdown(challenge.get("description", "Write your Python code below."))

# Split code input and theoretical analysis panes
col1, col2 = st.columns(2)

with col1:
    st.write("✏️ **Write / Complete Your Code:**")
    code_submission = st.text_area(
        "Python Code Editor",
        value=challenge.get("starter_code", ""),
        height=320,
        label_visibility="collapsed"
    )

with col2:
    st.write("💡 **Theoretical Explanation / Logic Proof:**")
    st.caption("Explain your choice of data structure, complexity parameters, or troubleshoot deduction below:")
    theoretical_proof = st.text_area(
        "Explanation Box",
        value="1. Logic explanation:\n\n2. Time Complexity: O(...)\n3. Space Complexity: O(...)",
        height=300,
        label_visibility="collapsed"
    )

st.write("---")

# Submit Trigger
submit_btn = st.button("🚀 Submit to AI Python Tutor", use_container_width=True)

# --- Action Logic: Evaluation & Sync ---
if submit_btn:
    prompt = f"""
    Target Challenge: {challenge.get('title')}
    Target Day: {day_id}
    Challenge Format: {challenge_type}
    
    Challenge Context & Description:
    {challenge.get('description')}
    
    Starter / Template Provided:
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
        "Act as a patient, encouraging AI Python Tutor. Evaluate the student's submission based on the 'Challenge Format' parameter:\n"
        "1. If challenge format is 'write_code': Grade functional correctness, clean variable naming, and appropriate algorithms.\n"
        "2. If challenge format is 'fill_code': Inspect if they correctly identified and completed the blanks (often represented as '___' or placeholders) in the starter template to make the program function.\n"
        "3. If challenge format is 'troubleshoot': Check if they successfully debugged the syntax errors, index bugs, or logical anomalies of the initial buggy draft.\n\n"
        "Weights:\n"
        "- Functional Correctness & Completion (40%)\n"
        "- Pythonic Conventions & PEP 8 Guidelines (30%)\n"
        "- Cleanliness, Naming & Structure (20%)\n"
        "- Conceptual Explanations in the proof (10%)\n\n"
        "Provide a strict total integer score out of 100.\n\n"
        "GRADUATED RESPONSE RULES:\n"
        "- If the Score is LESS THAN 85%:\n"
        "  - Praise their effort but state they did not meet requirements yet.\n"
        "  - You MUST construct a gentle Socratic Hint (`socratic_hint`). Point them in the right direction using leading questions (e.g. 'What happens if the input is an empty list?') instead of giving the answer away.\n"
        "  - The field `refactored_code` MUST remain completely empty.\n"
        "  - Set `passed = false`.\n"
        "- If the Score is 85% OR GREATER:\n"
        "  - Praise their excellent standard.\n"
        "  - You MUST write the optimal, PEP 8 compliant, comments-documented Python solution inside the `refactored_code` field.\n"
        "  - Set `passed = true`."
    )
    
    if "OpenAI" in active_engine:
        if not openai_key:
            st.error("❌ Cannot evaluate. OpenAI API key is missing. Add it in the sidebar overrides to proceed.")
        else:
            with st.spinner("🕵️ OpenAI Python Tutor is reviewing your code..."):
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=openai_key)
                    
                    completion = client.beta.chat.completions.parse(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        response_format=EvaluationResult,
                        temperature=0.1
                    )
                    
                    res_data = json.loads(completion.choices[0].message.content)
                    st.session_state["eval_result"] = res_data
                    st.success("✅ Code evaluation complete!")
                except Exception as e:
                    st.error(f"Failed to evaluate submission with OpenAI: {e}")
                    st.session_state["eval_result"] = None
    else: # Gemini
        if not gemini_key:
            st.error("❌ Cannot evaluate. Google Gemini API key is missing. Add it in the sidebar overrides to proceed.")
        else:
            with st.spinner("🕵️ Gemini Python Tutor is reviewing your code..."):
                try:
                    client = genai.Client(api_key=gemini_key)
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
                    
                    res_data = json.loads(response.text)
                    st.session_state["eval_result"] = res_data
                    st.success("✅ Code evaluation complete!")
                except Exception as e:
                    st.error(f"Failed to evaluate submission with Gemini: {e}")
                    st.session_state["eval_result"] = None

# --- Display Results ---
if "eval_result" in st.session_state and st.session_state["eval_result"]:
    res = st.session_state["eval_result"]
    passed = res.get("passed", False)
    score = res.get("score", 0)
    
    # 1. Header Metrics Card
    if passed:
        st.success(f"### 🎉 PASSED! Score: {score}/100")
    else:
        st.warning(f"### ⚠️ REDO - Score: {score}/100")
        
    # 2. Detailed Breakdown Grid
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🧩 Functional Correctness")
        st.write(res.get("functional_correctness_feedback", ""))
        
        st.markdown("#### 📐 Cleanliness & PEP 8 Style")
        st.write(res.get("cleanliness_feedback", ""))
        
    with c2:
        st.markdown("#### ⚡ Efficiency & Pythonic Practices")
        st.write(res.get("efficiency_feedback", ""))
        
        st.markdown("#### 🧠 Conceptual Understanding")
        st.write(res.get("rigor_feedback", ""))
        
    # Socratic Hint or Refactored Code display
    if not passed:
        st.info(f"💡 **Tutor Socratic Hint:**\n{res.get('socratic_hint')}")
    else:
        st.markdown("#### 🐍 Optimal Python Solution:")
        st.code(res.get("refactored_code"), language="python")
        
    # --- Supabase Database Sync Logic ---
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            db_data = {
                "user_id": user_id,
                "day_id": day_id,
                "completed": passed,
                "score": score,
                "code_submission": code_submission,
                "feedback": f"Score: {score} | Passed: {passed}. " + res.get("functional_correctness_feedback", "")[:200]
            }
            
            # Upsert using composite unique constraint
            supabase_client.table("python_portal_progress").upsert(db_data, on_conflict="user_id,day_id").execute()
            st.toast("☁️ Progress synced to database successfully!")
        except Exception as db_err:
            st.error(f"Database Cloud Sync: Failed to sync: {db_err} ❌")

    # --- HTML5 Cross-Origin postMessage Script Trigger ---
    # Notifies the parent frame on unifiedindex.com of the results
    feedback_snippet = res.get("functional_correctness_feedback", "")[:120].replace("'", "\\'")
    
    post_message_js = f"""
    <script>
        const messageData = {{
            type: 'SDE_PORTAL_EVALUATION', // uses same protocol listener for parent compatibility
            day_id: '{day_id}',
            score: {score},
            completed: {'true' if passed else 'false'},
            feedback: 'Python Tutor Score: {score} - {feedback_snippet}...'
        }};
        window.parent.postMessage(messageData, '*');
        console.log("Transmitted messageData to parent dashboard frame:", messageData);
    </script>
    """
    st.components.v1.html(post_message_js, height=0, width=0)
