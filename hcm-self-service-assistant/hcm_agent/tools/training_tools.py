"""Tools for training session discovery, enrollment, and cancellation."""

import pandas as pd
from datetime import datetime
from langchain_core.tools import tool

from hcm_agent.config.settings import TRAINING_SESSIONS_PATH, TRAINING_ENROLLMENTS_PATH


# ── Internal helpers ───────────────────────────────────────────────

def _next_enrollment_id(df: pd.DataFrame) -> str:
    if df.empty:
        return "ENR-001"
    nums = df["enrollment_id"].astype(str).str.replace("ENR-", "", regex=False).astype(int)
    return f"ENR-{nums.max() + 1:03d}"


# ── Tools ──────────────────────────────────────────────────────────

@tool
def list_available_trainings(category: str = "") -> str:
    """List all training sessions that still have seats available.

    Args:
        category: Optional filter — aml_kyc, compliance_regulatory,
                  risk_management, technical_skills, leadership_management,
                  customer_service. Leave blank to list all.

    Returns:
        Formatted list of available training sessions.
    """
    df = pd.read_csv(TRAINING_SESSIONS_PATH)

    if category.strip():
        df = df[
            df["category"].str.lower().str.replace(" ", "_")
            == category.lower().replace(" ", "_")
        ]

    available = df[df["seats_available"].astype(int) > 0]

    if available.empty:
        suffix = f" in category '{category}'" if category.strip() else ""
        return f"No training sessions with open seats{suffix}."

    lines = ["Available Training Sessions:"]
    for _, row in available.iterrows():
        flag = " 🔴 [MANDATORY]" if str(row.get("mandatory", "")).upper() == "TRUE" else ""
        lines.append(
            f"\n  [{row['course_id']}] {row['course_name']}{flag}"
            f"\n    Category   : {row['category']}"
            f"\n    Date/Time  : {row['date_slot']}"
            f"\n    Duration   : {row['duration_hours']} hours"
            f"\n    Instructor : {row['instructor']}"
            f"\n    Location   : {row['location']}"
            f"\n    Seats left : {int(row['seats_available'])} / {int(row['seats_total'])}"
        )
    return "\n".join(lines)


@tool
def get_training_details(course_id: str) -> str:
    """Get full details for a specific training course.

    Args:
        course_id: Course identifier (e.g. TRN001)

    Returns:
        Detailed course information.
    """
    df = pd.read_csv(TRAINING_SESSIONS_PATH)
    df["course_id"] = df["course_id"].astype(str).str.strip()

    record = df[df["course_id"] == course_id.strip()]
    if record.empty:
        return f"No training course found with ID '{course_id}'."

    row = record.iloc[0]
    mandatory = (
        "Yes — mandatory for all employees"
        if str(row.get("mandatory", "")).upper() == "TRUE"
        else "No"
    )

    return (
        f"Training Details — {row['course_id']}\n"
        f"  Name       : {row['course_name']}\n"
        f"  Category   : {row['category']}\n"
        f"  Date/Time  : {row['date_slot']}\n"
        f"  Duration   : {row['duration_hours']} hours\n"
        f"  Instructor : {row['instructor']}\n"
        f"  Location   : {row['location']}\n"
        f"  Mandatory  : {mandatory}\n"
        f"  Seats      : {int(row['seats_available'])} available / {int(row['seats_total'])} total\n"
        f"  Description: {row.get('description', 'N/A')}"
    )


@tool
def enroll_in_training(emp_id: str, course_id: str) -> str:
    """Enroll an employee in a training session.

    Args:
        emp_id:    Employee ID (e.g. EMP001)
        course_id: Course ID to enroll in (e.g. TRN003)

    Returns:
        Enrollment confirmation or an error message.
    """
    try:
        # ── Validate course & seat availability ────────────────────
        ses_df = pd.read_csv(TRAINING_SESSIONS_PATH)
        ses_df["course_id"] = ses_df["course_id"].astype(str).str.strip()
        mask = ses_df["course_id"] == course_id.strip()

        if not mask.any():
            return f"Course '{course_id}' not found."

        course    = ses_df[mask].iloc[0]
        course_ix = ses_df[mask].index[0]

        if int(course["seats_available"]) <= 0:
            return f"❌ '{course['course_name']}' is fully booked. No seats available."

        # ── Check for duplicate active enrollment ──────────────────
        enr_df = pd.read_csv(TRAINING_ENROLLMENTS_PATH)
        enr_df["emp_id"]    = enr_df["emp_id"].astype(str).str.strip()
        enr_df["course_id"] = enr_df["course_id"].astype(str).str.strip()

        already = enr_df[
            (enr_df["emp_id"]    == emp_id.strip()) &
            (enr_df["course_id"] == course_id.strip()) &
            (enr_df["status"]    == "Enrolled")
        ]
        if not already.empty:
            return f"You are already enrolled in '{course['course_name']}'."

        # ── Add enrollment record ──────────────────────────────────
        new_enr = {
            "enrollment_id":   _next_enrollment_id(enr_df),
            "emp_id":          emp_id.strip(),
            "course_id":       course_id.strip(),
            "enrollment_date": datetime.now().strftime("%Y-%m-%d"),
            "status":          "Enrolled",
        }
        enr_df = pd.concat([enr_df, pd.DataFrame([new_enr])], ignore_index=True)
        enr_df.to_csv(TRAINING_ENROLLMENTS_PATH, index=False)

        # ── Decrement seat ─────────────────────────────────────────
        ses_df.loc[course_ix, "seats_available"] = int(course["seats_available"]) - 1
        ses_df.to_csv(TRAINING_SESSIONS_PATH, index=False)

        return (
            f"✅ Successfully enrolled in '{course['course_name']}'!\n"
            f"   Date     : {course['date_slot']}\n"
            f"   Location : {course['location']}\n"
            f"Please add this to your calendar and inform your manager."
        )

    except Exception as exc:
        return f"Error enrolling in training: {exc}"


@tool
def cancel_training_enrollment(emp_id: str, course_id: str) -> str:
    """Cancel an employee's training enrollment and release the seat.

    Args:
        emp_id:    Employee ID
        course_id: Course ID to cancel enrollment from

    Returns:
        Cancellation confirmation or an error message.
    """
    try:
        enr_df = pd.read_csv(TRAINING_ENROLLMENTS_PATH)
        enr_df["emp_id"]    = enr_df["emp_id"].astype(str).str.strip()
        enr_df["course_id"] = enr_df["course_id"].astype(str).str.strip()

        mask = (
            (enr_df["emp_id"]    == emp_id.strip()) &
            (enr_df["course_id"] == course_id.strip()) &
            (enr_df["status"]    == "Enrolled")
        )

        if not mask.any():
            return f"No active enrollment found for course '{course_id}' for employee '{emp_id}'."

        enr_df.loc[mask, "status"] = "Cancelled"
        enr_df.to_csv(TRAINING_ENROLLMENTS_PATH, index=False)

        # ── Restore seat ───────────────────────────────────────────
        ses_df = pd.read_csv(TRAINING_SESSIONS_PATH)
        ses_df["course_id"] = ses_df["course_id"].astype(str).str.strip()
        ses_mask = ses_df["course_id"] == course_id.strip()

        course_name = course_id
        if ses_mask.any():
            c_ix = ses_df[ses_mask].index[0]
            ses_df.loc[c_ix, "seats_available"] = int(ses_df.loc[c_ix, "seats_available"]) + 1
            ses_df.to_csv(TRAINING_SESSIONS_PATH, index=False)
            course_name = ses_df[ses_mask].iloc[0]["course_name"]

        return f"✅ Enrollment in '{course_name}' has been cancelled. Your seat has been released."

    except Exception as exc:
        return f"Error cancelling training enrollment: {exc}"


@tool
def get_my_training_enrollments(emp_id: str) -> str:
    """List all training sessions an employee is currently enrolled in.

    Args:
        emp_id: Employee ID

    Returns:
        List of active enrollments with course details.
    """
    enr_df = pd.read_csv(TRAINING_ENROLLMENTS_PATH)
    enr_df["emp_id"] = enr_df["emp_id"].astype(str).str.strip()

    active = enr_df[
        (enr_df["emp_id"] == emp_id.strip()) &
        (enr_df["status"] == "Enrolled")
    ]

    if active.empty:
        return f"Employee '{emp_id}' is not currently enrolled in any training sessions."

    ses_df = pd.read_csv(TRAINING_SESSIONS_PATH)
    ses_df["course_id"] = ses_df["course_id"].astype(str).str.strip()

    lines = [f"Active Training Enrollments for {emp_id}:"]
    for _, row in active.iterrows():
        cid    = row["course_id"].strip()
        course = ses_df[ses_df["course_id"] == cid]
        if not course.empty:
            c = course.iloc[0]
            lines.append(
                f"  [{c['course_id']}] {c['course_name']}"
                f" | {c['date_slot']} | {c['location']}"
            )
        else:
            lines.append(f"  [{cid}] (details unavailable)")

    return "\n".join(lines)
