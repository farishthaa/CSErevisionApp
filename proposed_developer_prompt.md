# Master Prompt Template: Building a Decoupled AI Portal

This document contains a comprehensive template prompt that you can feed into **Antigravity** (or any advanced AI coding agent) to build another similar portal from scratch. It incorporates all security, embedding, database, and cross-origin communication rules discovered during our implementation.

---

```markdown
# Role & Goal
You are an expert full-stack software engineer. Your goal is to build a decoupled, secure, and production-grade education portal featuring a static client dashboard, an embedded Python AI grading sandbox, and a PostgreSQL database backend. 

## Architectural Framework
The application must be split into two isolated layers to prevent API credential leaks and ensure zero-maintenance static hosting:
1. **Frontend Layer (Static Dashboard)**: A responsive vanilla HTML5/CSS3/JS website. No node build steps or frameworks (like React). Designed with premium dark glassmorphism (slate-950 background, deep indigo accents).
2. **Backend Layer (Interactive Sandbox)**: A Python Streamlit app running in a cloud VM (like Streamlit Cloud) that integrates with LLMs (Google Gemini / OpenAI) to grade code submissions.
3. **Database Layer (Supabase)**: A PostgreSQL database to track scores and completion records.

---

## Technical Specifications & Pitfalls Checklist

### 1. Iframe Embedding & CORS Configuration (CRITICAL)
To prevent embedding loops, browser CORS blocks, or clickjacking redirects when the Streamlit backend is embedded in the frontend iframe:
* **Url parameter**: The frontend iframe source URL MUST append the `?embed=true` parameter. Example: `https://your-app.streamlit.app/?embed=true&day_id=day_1&user_id=alice`
* **Server Configurations**: You must create a `.streamlit/config.toml` file in both the root and backend folders containing:
  ```toml
  [server]
  enableCORS = false
  enableXsrfProtection = false
  ```

### 2. Dual-Engine AI Architecture
The backend evaluator must support a **Dual-Engine** design to provide failover security if one LLM provider is overloaded (e.g. Gemini Free Tier 503 errors):
* Support **OpenAI (`gpt-4o-mini`)** and **Google Gemini (`gemini-3.5-flash`)**.
* Use a sidebar selection dropdown allowing the user to select the active engine.
* Structure outputs using Pydantic models for both SDKs.
  * For OpenAI, use: `client.beta.chat.completions.parse`
  * For Gemini, use: `types.GenerateContentConfig(response_schema=EvaluationResult, response_mime_type="application/json")`

### 3. API Key & Security Isolation
* **Zero Keys in Client**: The frontend dashboard JS/HTML must contain zero LLM API keys.
* **Streamlit UI Key Masking**: Do NOT show API keys in plain text in the sidebar text boxes. If a key is pre-loaded on the server (via `.env` or Streamlit Secrets), the textbox value must be empty (`value=""`), and the placeholder must be set to `••••••••••••••••`.
* **Git Hygiene**: Add `.env` and `.venv` to the `.gitignore` immediately before writing any files.

### 4. Cross-Origin Communication
Because the frontend and backend are hosted on separate domains, direct browser DOM manipulation is blocked. You must use the **HTML5 `postMessage` protocol**:
* The child Streamlit iframe executes Javascript upon successful code grading:
  ```javascript
  window.parent.postMessage({
      type: 'PORTAL_EVALUATION_SUCCESS',
      day_id: 'day_x',
      score: score_integer,
      completed: true,
      feedback: '...'
  }, '*');
  ```
* The parent static dashboard listens for the event, saves the progress to LocalStorage, checks off the curriculum list, and refreshes the stats UI.

### 5. PostgreSQL Upsert Constraints
To prevent database locks and "unique constraint violation" errors on the database progress table:
* The progress table schema must feature a composite unique index on user and day:
  ```sql
  ALTER TABLE progress_table ADD CONSTRAINT unique_user_day UNIQUE (user_id, day_id);
  ```
* The python client upsert routine must explicitly declare this target to resolve conflicts:
  ```python
  supabase_client.table("progress_table").upsert(data, on_conflict="user_id,day_id").execute()
  ```

---

## Step-by-Step Implementation Plan

### Step 1: Initialize Git and Env Variables
Create `.gitignore` first. Define `.env.example` templates for both the root and backend paths.

### Step 2: Build the Database Schema
Write a `schema.sql` declaring a table `sde_portal_progress` containing fields: `id` (uuid), `user_id` (varchar), `day_id` (varchar), `completed` (boolean), `score` (int), `code_submission` (text), `feedback` (text), and `updated_at` (timestamp). Include the unique composite key constraint.

### Step 3: Implement the Streamlit Backend
Create `backend/streamlit_app.py` with:
* Key extraction from `os.getenv` or `st.secrets`.
* Expander controls for advanced overrides.
* Structured AI evaluator using the prompt-instruction template rules.
* Auto-trigger javascript `postMessage` script upon grading.

### Step 4: Implement the Static Frontend Dashboard
Create `frontend/index.html` and `frontend/app.js`:
* Read curriculum material from a JSON database.
* Implement tab routing: Reading, Practice Sandbox (iframe), and Stats/History.
* Integrate local cache fallback (using localStorage) to ensure functionality even if database configurations are blank.
* Append the event listeners for cross-origin messages.
```
