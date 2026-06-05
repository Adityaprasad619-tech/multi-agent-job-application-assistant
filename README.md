# Multi-Agent Job Application Assistant

The Multi-Agent Job Application Assistant is a professional tool designed to automate the process of federal job discovery, resume-to-job matching, and tailored application package generation. Built for candidates seeking positions on USAJobs, it uses a multi-agent orchestrator to align candidate profiles with job requirements. The application is built using Streamlit for the user interface, CrewAI for agent coordination, Groq for high-performance inference, and SQLite for secure multi-user data persistence.

---

## Key Features

- **Resume Upload & Parsing (PDF/DOCX)**: Automatically extracts text from uploaded resume documents using PyPDF and python-docx.
- **Structured Resume Profile Extraction**: Uses specialized agents to parse unstructured resume text into a schema-validated, queryable resume profile.
- **ATS Match Scoring**: Calculates matching scores deterministically using taxonomy-based keyword matching and normalization.
- **Resume Gap Analysis**: Performs gap analysis to identify missing skills, qualifications, and domain experience required for specific listings.
- **Resume Tailoring Recommendations**: Generates concrete resume modifications to align the candidate's profile with required job competencies.
- **Cover Letter Generation**: Generates targeted, professional cover letters that highlight the candidate's matching experience.
- **Recruiter Outreach Generation**: Generates outreach templates including LinkedIn messages, recruiter emails, and follow-up templates.
- **Application History Management**: Logs applied positions, candidate profiles, and generated materials.
- **Archive / Restore / Delete Workflows**: Supports full application lifecycle management, including soft-deletion (archive) and permanent deletion.
- **PDF Export**: Exports tailored cover letters and resume adjustment guides into professional PDF format.
- **TEST_MODE**: Local testing mode that bypasses external API calls using deterministic mock data generators.
- **Authentication & User Isolation**: Built-in support for secure email/password auth (SQLite+bcrypt) and external authentication (Clerk).

---

## System Architecture

The following diagram illustrates the sequential data flow of the application:

```
Resume Upload
      │
      ▼
Resume Profile Extraction (CrewAI Profile Extractor Agent)
      │
      ▼
Job Search (USAJobs API integration)
      │
      ▼
Job Analysis (CrewAI Job Analyzer Agent)
      │
      ▼
ATS Scoring (Deterministic matching against normalized skill taxonomy)
      │
      ▼
Gap Analysis (CrewAI Gap Analyst Agent)
      │
      ▼
Resume Recommendations (CrewAI Resume Specialist Agent)
      │
      ▼
Cover Letter Generation (CrewAI Resume Specialist Agent)
      │
      ▼
Outreach Generation (CrewAI Outreach Specialist Agent)
      │
      ▼
Persistence & History (SQLite database storage with user isolation)
```

### Component Roles

- **Streamlit**: Renders the user interface, manages application session state, and displays results dashboards.
- **CrewAI**: Orchestrates a team of autonomous agents using sequential process coordination, passing context between tasks.
- **Groq**: Provides low-latency API access to large language models (Llama 3.3 70B) for token-efficient text analysis.
- **SQLite**: Persists structured user accounts, resume profiles, search history, and generated application packages.
- **Pydantic**: Enforces strict structural type safety for all agent outputs and resume schemas.

---

## Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python** | Primary development language |
| **Streamlit** | Interactive front-end dashboard and UI |
| **CrewAI** | Multi-agent task planning and execution framework |
| **Groq** | Fast inference hosting provider for LLMs |
| **LiteLLM** | Unified LLM translation interface |
| **SQLite** | Local relational data persistence |
| **Pydantic** | Schema validation and structured LLM JSON extraction |
| **ReportLab** | PDF generation and formatting engine |
| **PyPDF** | PDF text extraction service |
| **python-docx** | DOCX document text parsing |

---

## Project Structure

```
multi-agent-job-application-assistant/
├── agents/             # CrewAI agent definitions and system prompts
├── auth/               # Authentication providers (Local SQLite, Clerk)
├── crews/              # Multi-agent crew orchestrations (Job search, Resume profile extraction)
├── database/           # SQLite database schema, managers, and migration scripts
├── schemas/            # Pydantic schemas (Agent outputs, ATS scores, Resume profile)
├── services/           # External integrations (USAJobs API, ATS scoring, Export, LLM client, normalizer)
├── tasks/              # CrewAI task templates and factories
├── tests/              # Pytest unit and integration test suites
├── ui/                 # Reusable Streamlit pages and dashboard components
├── utils/              # Configuration managers and logger configurations
├── app.py              # Application main entry point
├── requirements.txt    # Python project dependencies
└── .env.example        # Environment variable template
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Adityaprasad619-tech/multi-agent-job-application-assistant.git
   cd multi-agent-job-application-assistant
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Create a `.env` file by copying the template:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and input your credentials (see the [Environment Variables](#environment-variables) section below).

5. **Run Database Migrations**
   Initialize or migrate the SQLite database structure:
   ```bash
   python -m database.migrate
   ```

6. **Launch the Streamlit Application**
   ```bash
   streamlit run app.py
   ```

---

## Environment Variables

| Variable | Description | Default / Placeholder | Required |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | API key from Groq Console | `your_groq_api_key_here` | Yes |
| `USAJOBS_API_KEY` | Developer API key from USAJobs portal | `your_usajobs_api_key_here` | Yes |
| `USAJOBS_EMAIL` | Email address registered for USAJobs API | `your_email@example.com` | Yes |
| `GROQ_MODEL_NAME` | Model identifier to request from Groq | `llama-3.3-70b-versatile` | No |
| `AUTH_PROVIDER` | Authentication layer config (`local` or `clerk`) | `local` | No |
| `DATABASE_PATH` | File path relative to project root for SQLite db | `database/job_search.db` | No |
| `TEST_MODE` | Boolean flag to bypass live LLM API calls | `true` | No |

---

## Running the Application

### Development Mode
To develop, debug, or verify UI changes without consuming Groq LLM API limits, set `TEST_MODE=true` in your `.env` file.
- **Behavior**: USAJobs API remains active, but agent runs immediately return pre-generated mock application packages.
- **Benefits**: Near-instant feedback, no rate limits, zero API cost.

### Production Mode
For real-world analysis, set `TEST_MODE=false` in your `.env` file.
- **Behavior**: The application triggers live CrewAI orchestrations using the Groq API key and selected model.
- **Benefits**: Generates tailored resumes, customized cover letters, and outreach messaging based on uploaded data.

---

## Testing

Unit and integration tests are managed using `pytest`. Run the full test suite with:

```bash
python -m pytest
```

### Test Coverage
- **ATS Match Tests**: Verifies correctness of deterministic keyword mapping, parent-child skill taxonomies, and partial matches.
- **Resume Parsing Tests**: Validates PyPDF and python-docx text extraction edge cases.
- **Schema Validation Tests**: Checks Pydantic schema validation for profile structures and agent output schemas.
- **Mock Workflow Tests**: Confirms that the integration flow runs correctly in development mode.
- **Rate-Limit Resilience Tests**: Mocks provider API limits to verify exponential backoff, retry loops, and UI callbacks.

---

## Screenshots

### Login
*(Placeholder for authentication interface screenshot)*

### Resume Upload
*(Placeholder for resume processing dashboard screenshot)*

### ATS Dashboard
*(Placeholder for job results and ATS scoring breakdown screenshot)*

### Generated Materials
*(Placeholder for tailored cover letters and outreach templates screenshot)*

### Application History
*(Placeholder for application archiving and lifecycles dashboard screenshot)*

---

## Design Decisions

- **Structured Resume Profile**: Instead of injecting raw resume text into every agent prompt, the application extracts the resume into a structured Pydantic object (`StructuredResumeProfile`). This profile is saved in SQLite and serves as the single source of truth, minimizing token usage by over 48%.
- **Deterministic ATS Scoring**: Avoids unreliable LLM-based rating. Instead, it extracts required skills with the Job Analyzer agent, normalizes them via a custom mapping taxonomy, and calculates scores deterministically based on direct and partial matches.
- **Strict Pydantic Validation**: All outputs from LLM tasks are parsed into structured schemas. If an output violates type constraints, the custom parser catches it early and raises schema validation errors.
- **Soft-Delete Application Lifecycle**: Applications are archived by setting an `archived` database flag. This keeps the primary view clean while retaining historical metrics, allowing users to restore or permanently delete entries.
- **Token Optimization Strategy**: Leverages compact representations for intermediate matching and analysis tasks, reserving detailed profile formatting for the final drafting tasks (e.g., Cover Letter generation).

---

## Future Improvements

- **Application Status Tracking**: Add visual stages (Applied, Interviewing, Offered, Rejected) to manage applications.
- **Cloud Database Support**: Support PostgreSQL or MySQL backends for deployment.
- **Additional Job Providers**: Integrate external APIs (LinkedIn, Indeed) alongside USAJobs.
- **Advanced Analytics Dashboard**: Add dashboard metrics showing matching trends and skills gaps across target industries.
- **Multi-Model Support**: Support switching between Groq, OpenAI, and Anthropic backends dynamically.

---

## Resume Project Description

**Multi-Agent Job Application Assistant (Python, Streamlit, CrewAI, Groq, SQLite, Pydantic)**
- Engineered a multi-user job discovery and application tailoring platform using CrewAI agents and Groq LLMs.
- Designed a deterministic ATS matching engine with parent-child skill taxonomy mapping, reducing token consumption by 48% through a Pydantic-based Structured Resume Profile.
- Implemented robust rate-limit resilience with exponential retry policies and integrated a soft-delete database lifecycle management system.
- Authored a comprehensive integration and unit testing suite covering ATS scoring, parsing pipelines, and rate-resilience, achieving 100% test pass rates across 80+ test cases.

---


This project is licensed under the MIT License - see the LICENSE file for details.
