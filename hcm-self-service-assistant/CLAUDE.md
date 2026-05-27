# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Running the Project

```bash
# Install dependencies into a virtual environment
uv sync

# Launch the Streamlit UI (recommended for demos)
uv run streamlit run streamlit_app.py

# Run the plain CLI
uv run python main.py
```

Requires a `.env` file in the project root (copy from `.env.example`):
```
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o
TEMPERATURE=0
```

## Architecture

### Multi-Agent Supervisor Graph (`hcm_agent/workflows/graph.py`)
Implements the supervisor-router pattern:
- `START → supervisor` — classifies intent using structured output (`_SupervisorDecision` Pydantic model)
- Supervisor routes via `next_agent` to one of: `leave_agent`, `training_agent`, `policy_agent`, `info_agent`, or `END`
- Each agent has its own `ToolNode` with a restricted tool set (principle of least privilege)
- Each agent loops: `agent → tools → agent` until no tool calls remain, then routes to `END`

### State (`hcm_agent/models/state.py`)
`HCMState` is a `TypedDict` with:
- `messages` — append-only list (uses `operator.add` reducer)
- `intent`, `next_agent` — supervisor routing fields
- `emp_id` — employee context injected from UI / CLI
- Leave fields: `leave_type`, `leave_start_date`, `leave_end_date`, `leave_request_id`
- Training fields: `course_id`
- Result fields: `operation_success`, `operation_message`, `final_response`

### Tools

**Leave read** (`hcm_agent/tools/leave_reader.py`):
- `get_leave_balance` — balance by type for current year
- `get_leave_history` — all past and present requests
- `check_leave_balance_sufficient` — pre-check before submitting

**Leave write** (`hcm_agent/tools/leave_writer.py`):
- `submit_leave_request` — creates LR-YYYY-XXXX request, deducts balance
- `cancel_leave_request` — marks Cancelled, restores balance

**Training** (`hcm_agent/tools/training_tools.py`):
- `list_available_trainings` — with optional category filter
- `get_training_details` — full course info
- `enroll_in_training` — adds to training_enrollments.csv, decrements seat
- `cancel_training_enrollment` — marks Cancelled, restores seat
- `get_my_training_enrollments` — active enrollments for an employee

**Policy** (`hcm_agent/tools/policy_tools.py`):
- `search_hr_policy` — keyword search across title + content + category
- `list_policy_categories` — all categories with counts
- `get_policy_by_category` — full policies in a category

**Employee** (`hcm_agent/tools/employee_tools.py`):
- `get_employee_info` — profile from directory
- `list_employees_by_department` — all staff in a department

### Data Files

| File | Description |
|---|---|
| `employee_directory.csv` | Master employee list (10 employees across 8 departments) |
| `employee_leave_balances.csv` | Leave balances per employee per year |
| `leave_requests.csv` | Leave request history (mutable — tools write here) |
| `training_sessions.csv` | Training catalog with seat availability (mutable) |
| `training_enrollments.csv` | Individual enrollment records (mutable) |
| `hr_policies.csv` | HR policy content — Annual Leave, Sick Leave, Maternity/Paternity, WFH, AML/KYC, Data Privacy, Performance, Code of Conduct, T&E, Grievance |

### Configuration (`hcm_agent/config/settings.py`)
All CSV paths are resolved relative to `PROJECT_ROOT` via `Path(__file__).resolve().parent.parent.parent`.

### Message Sanitization (`hcm_agent/utils.py`)
`sanitize_messages()` replaces empty / None content with `" "` before every LLM call — a defensive guard against API rejections.
