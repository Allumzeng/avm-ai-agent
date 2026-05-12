# src/reporting/tools.py
from src.reporting.models import ReportState

REPORT_TOOLS = [
    {
        "name": "generate_report",
        "description": (
            "Generate the complete AVM management report in markdown format. "
            "Call this ONCE with the full report after all anomalies have been flagged. "
            "Structure the report with: Executive Summary, Key Metrics Table, "
            "Detailed Analysis by cost object, Hidden Costs section (capital cost, "
            "risk cost, inventory holding cost — include only if data is present), "
            "and Recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_text": {
                    "type": "string",
                    "description": "Full report in GitHub-flavored markdown.",
                },
            },
            "required": ["report_text"],
        },
    },
    {
        "name": "flag_anomaly",
        "description": (
            "Flag a notable finding that deserves immediate user attention. "
            "Call this for each anomaly BEFORE calling generate_report. "
            "Trigger conditions: negative net margin for any cost object; "
            "idle capacity exceeding 20% of normal capacity at any activity center; "
            "non-value-added activities exceeding 30% of total activity cost; "
            "any customer or product with large revenue but negative long-term value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "anomaly": {
                    "type": "string",
                    "description": "One clear sentence describing the anomaly, e.g. 'Customer Alpha generates NT$2M revenue but carries NT$2.4M in fully-allocated costs, yielding a -20% margin.'",
                },
            },
            "required": ["anomaly"],
        },
    },
]


def dispatch_report_tool(name: str, input_data: dict, state: ReportState) -> str:
    if name == "generate_report":
        state.report_text = input_data["report_text"]
        state.is_complete = True
        return "Report generated and stored."

    if name == "flag_anomaly":
        state.anomalies.append(input_data["anomaly"])
        return f"Anomaly flagged: {input_data['anomaly']}"

    return f"Unknown report tool: {name}"
