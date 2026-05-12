from typing import Callable
from src.wizard.state import WizardState

WIZARD_TOOLS = [
    {
        "name": "search_avm_knowledge",
        "description": (
            "Search the AVM knowledge base for context relevant to the current wizard step. "
            "Use this to retrieve module-specific content before asking the user a question, "
            "or to explain an AVM concept during the wizard. "
            "Optionally filter by module (1=Resource, 2=ActivityCenter, 3=Activity, 4=ValueObject)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query in the user's language."},
                "module_filter": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "Optional AVM module to restrict the search.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_wizard_data",
        "description": (
            "Save a validated piece of information collected from the user. "
            "Call this ONLY when the user has provided a clear, complete answer to a wizard question. "
            "If the answer is vague or incomplete, ask for clarification first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": (
                        "Descriptive field name, e.g. 'module1_expense_categories', "
                        "'module2_executors', 'symptom', 'root_cause_hypothesis'."
                    ),
                },
                "value": {
                    "description": "The extracted, structured data from the user's answer."
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "complete_wizard",
        "description": (
            "Call this when the wizard is fully done — all required information has been "
            "collected (Setup: all 4 modules; Diagnosis: symptom + follow-ups + diagnosis given). "
            "Provide a concise summary of everything collected or concluded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Summary of all collected data or diagnosis conclusions.",
                }
            },
            "required": ["summary"],
        },
    },
]


def dispatch_wizard_tool(
    name: str,
    input_data: dict,
    state: WizardState,
    retriever: Callable,
) -> str:
    if name == "save_wizard_data":
        key = input_data["key"]
        value = input_data["value"]
        state.collected_data[key] = value
        state.current_step += 1
        return f"Saved '{key}' to wizard state (step {state.current_step})."

    if name == "complete_wizard":
        state.is_complete = True
        return f"Wizard marked complete. Summary: {input_data.get('summary', '')}"

    if name == "search_avm_knowledge":
        query = input_data["query"]
        module_filter = input_data.get("module_filter")
        chunks = retriever(query, module_filter=module_filter)
        if not chunks:
            return "No relevant AVM knowledge found for this query."
        return "\n\n---\n\n".join(chunks)

    return f"Unknown wizard tool: {name}"
