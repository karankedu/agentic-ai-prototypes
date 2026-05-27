"""Read-only tools for employee directory lookups."""

import pandas as pd
from langchain_core.tools import tool

from hcm_agent.config.settings import EMPLOYEE_DIRECTORY_PATH


@tool
def get_employee_info(emp_id: str) -> str:
    """Get profile information for an employee from the directory.

    Args:
        emp_id: Employee ID (e.g. EMP001)

    Returns:
        Employee profile details.
    """
    df = pd.read_csv(EMPLOYEE_DIRECTORY_PATH)
    df["emp_id"] = df["emp_id"].astype(str).str.strip()

    record = df[df["emp_id"] == emp_id.strip()]
    if record.empty:
        return f"No employee found with ID '{emp_id}'."

    row = record.iloc[0]
    return (
        f"Employee Profile:\n"
        f"  Employee ID   : {row['emp_id']}\n"
        f"  Name          : {row['name']}\n"
        f"  Department    : {row['department']}\n"
        f"  Designation   : {row['designation']}\n"
        f"  Email         : {row['email']}\n"
        f"  Work Location : {row['work_location']}\n"
        f"  Join Date     : {row['join_date']}\n"
        f"  Reports To    : {row.get('manager_name', 'N/A')} ({row.get('manager_id', 'N/A')})"
    )


@tool
def list_employees_by_department(department: str) -> str:
    """List all employees in a given department.

    Args:
        department: Department name, e.g. 'Retail Banking', 'Compliance',
                    'IT Department', 'Risk Management', 'Treasury', 'HR',
                    'Operations', 'Audit & Control'

    Returns:
        List of employees in that department with their designations.
    """
    df = pd.read_csv(EMPLOYEE_DIRECTORY_PATH)

    results = df[
        df["department"].str.lower().str.contains(department.lower(), na=False)
    ]

    if results.empty:
        return f"No employees found in department '{department}'."

    lines = [f"Employees in {department}:"]
    for _, row in results.iterrows():
        lines.append(f"  {row['emp_id']}: {row['name']} — {row['designation']}")
    return "\n".join(lines)
