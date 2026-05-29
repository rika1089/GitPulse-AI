"""
llm/report_generator.py
-----------------------
Structured synthesis helpers used across services for final report assembly.
"""

from typing import List, Optional
from gitpulse_mcp.models.repository import RepoDetails, ActivityTimelineItem, Recommendation

def generate_markdown_report(repo_details: RepoDetails) -> str:
    """Generate a markdown report from a RepoDetails object."""
    repo = repo_details.repository
    insights = repo_details.insights

    lines = []
    lines.append(f"# Repository Assessment: {repo.owner}/{repo.name}")
    lines.append(f"**Health Score:** {repo.health_score}/100 ({repo.classification.value})")
    if repo.activity_status:
        lines.append(f"**Activity Level:** {repo.activity_status.value}")
    lines.append("")
    
    lines.append("## Summary")
    lines.append(insights.summary)
    lines.append("")

    if insights.strengths:
        lines.append("### Strengths")
        for s in insights.strengths:
            lines.append(f"- {s}")
        lines.append("")

    if insights.risks:
        lines.append("### Risks")
        for r in insights.risks:
            lines.append(f"- {r}")
        lines.append("")

    if insights.recommendations:
        lines.append("### Recommendations")
        for rec in insights.recommendations:
            lines.append(f"- **[{rec.impact.value.upper()}]** {rec.title} ({rec.category.value}): {rec.description}")
        lines.append("")

    # Add Quality checks summary
    lines.append("## Quality Checks")
    lines.append(f"- **README Quality:** {repo_details.readme_quality.score}/100")
    lines.append(f"- **Security:** {repo_details.security.score}/100")
    lines.append(f"- **CI/CD:** {repo_details.ci_cd.score}/100")
    lines.append(f"- **Contribution Health:** {repo_details.contribution_health.score}/100")
    lines.append("")

    return "\n".join(lines)

def format_timeline_for_prompt(timeline: List[ActivityTimelineItem]) -> str:
    """Format timeline events into a string suitable for LLM context."""
    if not timeline:
        return "No recent activity found."
    lines = []
    for item in timeline:
        lines.append(f"[{item.timestamp}] {item.type.value} - {item.title} by {item.user.name}")
    return "\n".join(lines)

def format_recommendations(recommendations: List[Recommendation]) -> str:
    """Format a list of recommendations."""
    if not recommendations:
        return "No recommendations."
    return "\n".join(
        f"- [{r.category.value}] ({r.impact.value} Impact) {r.title}: {r.description}"
        for r in recommendations
    )
