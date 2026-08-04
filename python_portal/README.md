# Python Teaching Portal

An interactive portal designed for teaching Python programming to computer science students. Supports complete code implementation, template completion ("fill in the blanks"), and syntax/logic troubleshooting.

---

## 1. Quick Start Local Development

### A. Environment Configuration
1. Navigate to the backend directory:
   ```bash
   cd python_portal/backend
   ```
2. Duplicate `.env.example` to create a local configuration file named `.env`:
   ```bash
   copy .env.example .env
   ```
3. Open `.env` and fill in your:
   - `GEMINI_API_KEY` (Google AI Studio)
   - `OPENAI_API_KEY` (OpenAI Platform)
   - `SUPABASE_URL` and `SUPABASE_KEY` (Supabase Postgres Database credentials)

### B. Python Setup & Execution
1. Install requirements inside the project virtual environment:
   ```bash
   uv pip install -r python_portal/backend/requirements.txt
   ```
2. Run the connection validation script:
   ```bash
   uv run python python_portal/backend/verify_apis.py
   ```
3. Launch the Streamlit backend evaluator server locally on port **`8502`** (to avoid port conflicts with the SDE portal on `8501`):
   ```bash
   uv run streamlit run python_portal/backend/streamlit_app.py --server.port 8502
   ```

### C. Frontend Launch
1. Open the file `python_portal/frontend/index.html` directly in your browser.
2. Click the **Settings ⚙️** icon in the sidebar and ensure the Streamlit URL is configured to:
   `http://localhost:8502`

---

## 2. Cloud Production Deployment

### A. Frontend Dashboard (Cloudflare Pages)
1. Go to your **Cloudflare Pages** dashboard.
2. Link the repository `farishthaa/CSErevisionApp`.
3. Set the **Root directory** to **`python_portal/frontend`** (to isolate it from the SDE folder).
4. Deploy the site and configure your custom subdomain (e.g., **`python.unifiedindex.com`**).

### B. Backend Evaluator (Streamlit Community Cloud)
1. Log in to **[share.streamlit.io](https://share.streamlit.io/)**.
2. Click **New app** and specify:
   - Repository: `farishthaa/CSErevisionApp`
   - Branch: `main`
   - Main file path: **`python_portal/backend/streamlit_app.py`**
3. Open **Advanced settings...** and paste your `.env` parameters inside the **Secrets** section:
   ```toml
   GEMINI_API_KEY = "your_key"
   OPENAI_API_KEY = "your_key"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-key"
   ```
4. Deploy the app. Copy the secure URL (e.g., `https://python-tutor.streamlit.app`).

### C. Link Them Together
Open `https://python.unifiedindex.com`, open **Settings ⚙️**, paste the secure Streamlit Cloud URL, and save the configuration!
