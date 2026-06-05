# 🎯 Multi-Agent Job Search System

AI-powered federal job search assistant using CrewAI, Groq, and USAJobs API.

## Architecture

```
Streamlit UI → USAJobs API → CrewAI Agents (Groq LLM) → SQLite
```

**Agents:**
1. **Job Analyzer** — Extracts skills, keywords, and ATS insights
2. **Resume & Cover Letter Specialist** — Tailored recommendations
3. **Networking & Outreach Specialist** — LinkedIn messages

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env with your API keys

# 4. Run
streamlit run app.py
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `USAJOBS_API_KEY` | ✅ | USAJobs API key |
| `USAJOBS_EMAIL` | ✅ | Email registered with USAJobs |
| `GROQ_MODEL_NAME` | ❌ | Defaults to `llama-3.3-70b-versatile` |

## Project Structure

```
├── agents/          # CrewAI agent definitions
├── tasks/           # Task definitions for each agent
├── crews/           # Crew orchestration
├── services/        # USAJobs API + LLM factory
├── database/        # SQLite persistence
├── ui/              # Streamlit UI components
├── utils/           # Config, logging
├── logs/            # Auto-generated log files
├── app.py           # Entry point
└── requirements.txt
```
