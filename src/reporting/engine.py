import anthropic
from src.agent.prompt import AVM_CORE_KNOWLEDGE
from src.reporting.models import ReportState, ReportType
from src.reporting.tools import REPORT_TOOLS, dispatch_report_tool

_REPORT_DESCRIPTIONS = {
    "profitability": (
        "Customer/Product Profitability Report — show revenue, fully-allocated cost "
        "(including AVM hidden costs: capital cost, risk cost, inventory holding cost where data is present), "
        "and net profit per customer and product. Flag customers or products with negative margins."
    ),
    "capacity": (
        "Capacity Analysis Report — compare normal capacity vs actual capacity by activity center, "
        "calculate idle capacity cost and over-utilization cost. "
        "Flag any activity center with idle capacity exceeding 20% of normal capacity."
    ),
    "attribute": (
        "Activity Attribute Dashboard — break down activity costs by the five AVM attribute types: "
        "quality (preventive / appraisal / internal failure / external failure), "
        "capacity (productive / non-productive / idle), "
        "value-added vs non-value-added, customer service stages, and ESG categories. "
        "Flag if non-value-added activities exceed 30% of total activity cost."
    ),
    "value_object": (
        "Value Object Report — analyze long-term vs short-term value per customer or product. "
        "Flag any value object where large revenue coexists with low or negative long-term value "
        "(the 'large client, actually unprofitable' AVM pattern)."
    ),
}


def _build_report_system_prompt(report_type: str, role: str) -> str:
    return f"""{AVM_CORE_KNOWLEDGE}

You are generating a {_REPORT_DESCRIPTIONS[report_type]}

The current user role is: {role}. Calibrate the level of detail accordingly.

Instructions:
1. First, call `flag_anomaly` for each significant finding you identify in the data.
2. Then call `generate_report` once with the complete structured report in GitHub-flavored markdown.
3. Report structure: Executive Summary → Key Metrics Table → Detailed Analysis by cost object → Hidden Costs (only if data present) → Recommendations.
4. Respond in the same language as the column headers of the uploaded data (Traditional Chinese if headers are in Chinese, English otherwise).
5. Do NOT produce any text outside of tool calls — all output goes through the tools."""


def _format_data_for_claude(source_data: dict) -> str:
    """Convert parsed data dict to a compact markdown table for Claude context."""
    lines = [f"**File:** {source_data.get('file_name', 'unknown')}"]
    for sheet_name, rows in source_data.get("sheets", {}).items():
        lines.append(f"\n### Sheet: {sheet_name} ({len(rows)} rows)")
        if not rows:
            continue
        headers = list(rows[0].keys())
        lines.append("| " + " | ".join(str(h) for h in headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        display_rows = rows[:50]
        for row in display_rows:
            lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
        if len(rows) > 50:
            lines.append(f"_... {len(rows) - 50} more rows truncated_")
    return "\n".join(lines)


class ReportingEngine:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, report_type: ReportType, source_data: dict, role: str) -> ReportState:
        state = ReportState(report_type=report_type, source_data=source_data)
        system = _build_report_system_prompt(report_type, role)
        data_text = _format_data_for_claude(source_data)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Here is the uploaded AVM data:\n\n{data_text}\n\n"
                    f"Please generate the {report_type} report."
                ),
            }
        ]

        while True:
            response = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=8192,
                system=system,
                messages=messages,
                tools=REPORT_TOOLS,
            )

            if response.stop_reason == "end_turn":
                return state

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_report_tool(block.name, block.input, state)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                raise RuntimeError(f"Unexpected stop_reason from Claude API: {response.stop_reason!r}")
