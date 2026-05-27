"""Read-only tools for leave balance and history lookups."""

import pandas as pd
from langchain_core.tools import tool

from hcm_agent.config.settings import LEAVE_BALANCES_PATH, LEAVE_REQUESTS_PATH


@tool
def get_leave_balance(emp_id: str) -> str:
    """Get the current leave balance for an employee.

    Args:
        emp_id: Employee ID (e.g. EMP001)

    Returns:
        A formatted summary of all leave balances for the current year.
    """
    df = pd.read_csv(LEAVE_BALANCES_PATH)
    df["emp_id"] = df["emp_id"].astype(str).str.strip()

    record = df[df["emp_id"] == emp_id.strip()]
    if record.empty:
        return f"No leave balance record found for employee ID '{emp_id}'."

    row = record.iloc[0]

    def _remaining(total_col: str, used_col: str) -> tuple[int, int, int]:
        total = int(row.get(total_col, 0))
        used  = int(row.get(used_col, 0))
        return total, used, total - used

    al_t, al_u, al_r = _remaining("annual_leave_total",    "annual_leave_used")
    sl_t, sl_u, sl_r = _remaining("sick_leave_total",       "sick_leave_used")
    el_t, el_u, el_r = _remaining("emergency_leave_total",  "emergency_leave_used")

    lines = [
        f"Leave Balance for {emp_id} (Year {int(row['year'])}):",
        f"  • Annual Leave   : {al_r} days remaining  (used {al_u} / {al_t})",
        f"  • Sick Leave     : {sl_r} days remaining  (used {sl_u} / {sl_t})",
        f"  • Emergency Leave: {el_r} days remaining  (used {el_u} / {el_t})",
    ]

    ml_t = int(row.get("maternity_leave_total", 0))
    if ml_t > 0:
        ml_u = int(row.get("maternity_leave_used", 0))
        lines.append(f"  • Maternity Leave: {ml_t - ml_u} days remaining  (used {ml_u} / {ml_t})")

    pl_t = int(row.get("paternity_leave_total", 0))
    if pl_t > 0:
        pl_u = int(row.get("paternity_leave_used", 0))
        lines.append(f"  • Paternity Leave: {pl_t - pl_u} days remaining  (used {pl_u} / {pl_t})")

    return "\n".join(lines)


@tool
def get_leave_history(emp_id: str) -> str:
    """Get the leave request history for an employee.

    Args:
        emp_id: Employee ID (e.g. EMP001)

    Returns:
        A list of all past and present leave requests.
    """
    df = pd.read_csv(LEAVE_REQUESTS_PATH)
    df["emp_id"] = df["emp_id"].astype(str).str.strip()

    records = df[df["emp_id"] == emp_id.strip()]
    if records.empty:
        return f"No leave history found for employee ID '{emp_id}'."

    lines = [f"Leave History for Employee {emp_id}:"]
    for _, row in records.iterrows():
        reason = f" | Reason: {row['reason']}" if str(row.get("reason", "")).strip() else ""
        lines.append(
            f"  [{row['request_id']}] {row['leave_type']} | "
            f"{row['start_date']} → {row['end_date']} ({int(row['days'])} days) | "
            f"Status: {row['status']}{reason}"
        )
    return "\n".join(lines)


@tool
def check_leave_balance_sufficient(emp_id: str, leave_type: str, days_requested: int) -> str:
    """Check whether an employee has enough leave balance for a request.

    Args:
        emp_id: Employee ID
        leave_type: Type of leave (annual_leave, sick_leave, emergency_leave,
                    maternity_leave, paternity_leave)
        days_requested: Number of working days required

    Returns:
        A message indicating whether the balance is sufficient.
    """
    df = pd.read_csv(LEAVE_BALANCES_PATH)
    df["emp_id"] = df["emp_id"].astype(str).str.strip()

    record = df[df["emp_id"] == emp_id.strip()]
    if record.empty:
        return f"No leave balance record found for employee ID '{emp_id}'."

    row   = record.iloc[0]
    lt    = leave_type.lower().replace(" ", "_")
    col_t = f"{lt}_total"
    col_u = f"{lt}_used"

    if col_t not in row.index:
        return (
            f"Leave type '{leave_type}' is not recognised. "
            "Valid types: annual_leave, sick_leave, emergency_leave, "
            "maternity_leave, paternity_leave."
        )

    available = int(row[col_t]) - int(row[col_u])
    if available >= days_requested:
        return (
            f"✅ Sufficient balance. Employee {emp_id} has {available} "
            f"{lt} days available. Requested: {days_requested} days."
        )
    return (
        f"❌ Insufficient balance. Employee {emp_id} has only {available} "
        f"{lt} days available. Requested: {days_requested} days."
    )
