"""Write tools for submitting and cancelling leave requests."""

import pandas as pd
from datetime import datetime, date as date_type
from langchain_core.tools import tool

from hcm_agent.config.settings import LEAVE_BALANCES_PATH, LEAVE_REQUESTS_PATH


# ── Internal helpers ───────────────────────────────────────────────

def _count_working_days(start_date: str, end_date: str) -> int:
    """Count Mon–Fri working days between two YYYY-MM-DD dates, inclusive."""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end   = datetime.strptime(end_date,   "%Y-%m-%d").date()
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:   # 0=Mon … 4=Fri
            count += 1
        current = date_type.fromordinal(current.toordinal() + 1)
    return count


def _next_request_id(df: pd.DataFrame) -> str:
    """Generate the next sequential LR-YYYY-XXXX request ID."""
    year   = datetime.now().year
    prefix = f"LR-{year}-"
    subset = df[df["request_id"].astype(str).str.startswith(prefix)]
    if subset.empty:
        return f"{prefix}0001"
    max_num = subset["request_id"].str.replace(prefix, "", regex=False).astype(int).max()
    return f"{prefix}{max_num + 1:04d}"


# ── Tools ──────────────────────────────────────────────────────────

@tool
def submit_leave_request(
    emp_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> str:
    """Submit a leave request for an employee.

    Args:
        emp_id:     Employee ID (e.g. EMP001)
        leave_type: Type of leave — annual_leave, sick_leave, emergency_leave,
                    maternity_leave, or paternity_leave
        start_date: Start date in YYYY-MM-DD format
        end_date:   End date in YYYY-MM-DD format
        reason:     Optional reason for the leave

    Returns:
        Confirmation with the generated request ID, or an error message.
    """
    try:
        lt = leave_type.lower().replace(" ", "_")

        days = _count_working_days(start_date, end_date)
        if days <= 0:
            return "Invalid date range — start date must be before end date and must include at least one working day."

        # ── Check balance ──────────────────────────────────────────
        bal_df = pd.read_csv(LEAVE_BALANCES_PATH)
        bal_df["emp_id"] = bal_df["emp_id"].astype(str).str.strip()
        emp_rows = bal_df[bal_df["emp_id"] == emp_id.strip()]

        if emp_rows.empty:
            return f"Employee '{emp_id}' not found in leave balance records."

        col_t = f"{lt}_total"
        col_u = f"{lt}_used"

        if col_t not in emp_rows.columns:
            return (
                f"Invalid leave type '{leave_type}'. "
                "Valid types: annual_leave, sick_leave, emergency_leave, "
                "maternity_leave, paternity_leave."
            )

        idx       = emp_rows.index[0]
        available = int(bal_df.loc[idx, col_t]) - int(bal_df.loc[idx, col_u])

        if available < days:
            return (
                f"❌ Insufficient {lt} balance. "
                f"Available: {available} day(s), Requested: {days} day(s)."
            )

        # ── Create request ─────────────────────────────────────────
        req_df     = pd.read_csv(LEAVE_REQUESTS_PATH)
        request_id = _next_request_id(req_df)

        new_row = {
            "request_id":  request_id,
            "emp_id":       emp_id.strip(),
            "leave_type":   lt,
            "start_date":   start_date,
            "end_date":     end_date,
            "days":         days,
            "status":       "Approved",   # auto-approved in this prototype
            "reason":       reason,
            "applied_date": datetime.now().strftime("%Y-%m-%d"),
            "approved_by":  "System",
        }
        req_df = pd.concat([req_df, pd.DataFrame([new_row])], ignore_index=True)
        req_df.to_csv(LEAVE_REQUESTS_PATH, index=False)

        # ── Deduct balance ─────────────────────────────────────────
        bal_df.loc[idx, col_u] = int(bal_df.loc[idx, col_u]) + days
        bal_df.to_csv(LEAVE_BALANCES_PATH, index=False)

        return (
            f"✅ Leave request submitted successfully!\n"
            f"   Request ID : {request_id}\n"
            f"   Type       : {lt}\n"
            f"   Dates      : {start_date} → {end_date} ({days} working day(s))\n"
            f"   Status     : Approved\n"
            f"Please inform your manager and update your team calendar."
        )

    except Exception as exc:
        return f"Error submitting leave request: {exc}"


@tool
def cancel_leave_request(request_id: str, emp_id: str) -> str:
    """Cancel an existing leave request and restore the leave balance.

    Args:
        request_id: The leave request ID (e.g. LR-2026-0001)
        emp_id:     Employee ID for ownership verification

    Returns:
        Confirmation of cancellation or an error message.
    """
    try:
        req_df = pd.read_csv(LEAVE_REQUESTS_PATH)
        req_df["request_id"] = req_df["request_id"].astype(str).str.strip()
        req_df["emp_id"]     = req_df["emp_id"].astype(str).str.strip()

        mask = (
            (req_df["request_id"] == request_id.strip()) &
            (req_df["emp_id"]     == emp_id.strip())
        )

        if not mask.any():
            return f"Leave request '{request_id}' not found for employee '{emp_id}'."

        row    = req_df[mask].iloc[0]
        status = str(row["status"])

        if status in ("Cancelled", "Rejected"):
            return f"Leave request '{request_id}' is already {status}. No action taken."

        days = int(row["days"])
        lt   = str(row["leave_type"]).lower().replace(" ", "_")

        # ── Mark cancelled ─────────────────────────────────────────
        req_df.loc[mask, "status"] = "Cancelled"
        req_df.to_csv(LEAVE_REQUESTS_PATH, index=False)

        # ── Restore balance ────────────────────────────────────────
        bal_df = pd.read_csv(LEAVE_BALANCES_PATH)
        bal_df["emp_id"] = bal_df["emp_id"].astype(str).str.strip()
        bal_mask = bal_df["emp_id"] == emp_id.strip()

        if bal_mask.any():
            col_u = f"{lt}_used"
            if col_u in bal_df.columns:
                bal_idx = bal_df[bal_mask].index[0]
                bal_df.loc[bal_idx, col_u] = max(
                    0, int(bal_df.loc[bal_idx, col_u]) - days
                )
                bal_df.to_csv(LEAVE_BALANCES_PATH, index=False)

        return (
            f"✅ Leave request '{request_id}' has been cancelled.\n"
            f"   {days} day(s) of {lt} have been restored to your balance."
        )

    except Exception as exc:
        return f"Error cancelling leave request: {exc}"
