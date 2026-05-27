import operator
from typing import Annotated, TypedDict


class HCMState(TypedDict):
    # Core conversation — append-only (operator.add reducer)
    messages: Annotated[list, operator.add]

    # Supervisor routing fields
    intent: str        # leave_management | training | policy_query | employee_info | unknown
    next_agent: str    # leave_agent | training_agent | policy_agent | info_agent | END

    # Employee context (injected from UI / CLI)
    emp_id: str

    # Leave management fields
    leave_type: str
    leave_start_date: str
    leave_end_date: str
    leave_request_id: str

    # Training fields
    course_id: str

    # Result / output fields
    operation_success: bool
    operation_message: str
    final_response: str
