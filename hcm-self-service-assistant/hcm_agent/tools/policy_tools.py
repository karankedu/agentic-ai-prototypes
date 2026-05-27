"""Read-only tools for querying the HR policy knowledge base."""

import pandas as pd
from langchain_core.tools import tool

from hcm_agent.config.settings import HR_POLICIES_PATH


@tool
def search_hr_policy(query: str) -> str:
    """Search HR policies by keyword or topic.

    Args:
        query: Search term, e.g. 'maternity leave', 'work from home',
               'performance review', 'AML', 'data privacy'

    Returns:
        Full content of matching HR policies.
    """
    df = pd.read_csv(HR_POLICIES_PATH)
    q  = query.lower()

    mask = (
        df["title"].str.lower().str.contains(q, na=False) |
        df["content"].str.lower().str.contains(q, na=False) |
        df["category"].str.lower().str.contains(q, na=False)
    )

    results = df[mask]
    if results.empty:
        return (
            f"No HR policies found matching '{query}'. "
            "Try different keywords or use list_policy_categories() to browse."
        )

    lines = [f"HR Policies matching '{query}':"]
    for _, row in results.iterrows():
        lines.append(
            f"\n{'─' * 60}"
            f"\n📋 {row['title']}"
            f"\n   Category     : {row['category']}"
            f"\n   Effective    : {row['effective_date']}"
            f"\n   Last Updated : {row['last_updated']}"
            f"\n\n{row['content']}"
        )
    return "\n".join(lines)


@tool
def list_policy_categories() -> str:
    """List all available HR policy categories.

    Returns:
        All categories with the count of policies in each.
    """
    df = pd.read_csv(HR_POLICIES_PATH)
    cats = df.groupby("category").size().reset_index(name="count")

    lines = ["Available HR Policy Categories:"]
    for _, row in cats.sort_values("category").iterrows():
        lines.append(f"  • {row['category']} ({int(row['count'])} policies)")
    return "\n".join(lines)


@tool
def get_policy_by_category(category: str) -> str:
    """Get all HR policies that belong to a specific category.

    Args:
        category: Policy category name, e.g. 'Leave Management',
                  'Compliance', 'Performance', 'Work Arrangements',
                  'Conduct', 'Travel and Expense', 'HR Processes'

    Returns:
        Full content of all policies in that category.
    """
    df = pd.read_csv(HR_POLICIES_PATH)

    results = df[df["category"].str.lower().str.contains(category.lower(), na=False)]
    if results.empty:
        return (
            f"No policies found for category '{category}'. "
            "Use list_policy_categories() to see available categories."
        )

    lines = [f"HR Policies — Category: {category}"]
    for _, row in results.iterrows():
        lines.append(
            f"\n{'─' * 60}"
            f"\n📋 {row['title']}"
            f"\n   Last Updated : {row['last_updated']}"
            f"\n\n{row['content']}\n"
        )
    return "\n".join(lines)
