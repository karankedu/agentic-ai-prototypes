from pathlib import Path

# Project root is 3 levels up from this file: hcm_agent/config/settings.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── CSV data paths ─────────────────────────────────────────────────
EMPLOYEE_DIRECTORY_PATH    = PROJECT_ROOT / "employee_directory.csv"
LEAVE_BALANCES_PATH        = PROJECT_ROOT / "employee_leave_balances.csv"
LEAVE_REQUESTS_PATH        = PROJECT_ROOT / "leave_requests.csv"
TRAINING_SESSIONS_PATH     = PROJECT_ROOT / "training_sessions.csv"
TRAINING_ENROLLMENTS_PATH  = PROJECT_ROOT / "training_enrollments.csv"
HR_POLICIES_PATH           = PROJECT_ROOT / "hr_policies.csv"

# ── Reference lists (informational, not used for runtime validation) ──
VALID_LEAVE_TYPES = [
    "annual_leave",
    "sick_leave",
    "emergency_leave",
    "maternity_leave",
    "paternity_leave",
]

VALID_TRAINING_CATEGORIES = [
    "aml_kyc",
    "compliance_regulatory",
    "risk_management",
    "technical_skills",
    "leadership_management",
    "customer_service",
]

VALID_DEPARTMENTS = [
    "Retail Banking",
    "Risk Management",
    "Compliance",
    "IT Department",
    "HR",
    "Treasury",
    "Operations",
    "Audit & Control",
]
