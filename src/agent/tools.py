from typing import Callable

TOOLS = [
    {
        "name": "search_avm_knowledge",
        "description": (
            "Search the AVM knowledge base for relevant information. "
            "Use this for any question about AVM concepts, modules, attributes, formulas, or methodology. "
            "Optionally filter by AVM module number (1=Resource, 2=ActivityCenter, 3=Activity, 4=ValueObject)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query in the user's language.",
                },
                "module_filter": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "Optional AVM module number to restrict search scope.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_user_context",
        "description": "Get the current user's role for calibrating response depth.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

def dispatch_tool(
    name: str,
    input_data: dict,
    retriever: Callable,
    role: str,
) -> str:
    if name == "search_avm_knowledge":
        query = input_data["query"]
        module_filter = input_data.get("module_filter")
        chunks = retriever(query, module_filter=module_filter)
        if not chunks:
            return "No relevant AVM knowledge found for this query."
        return "\n\n---\n\n".join(chunks)

    if name == "get_user_context":
        return f"Current user role: {role}"

    return f"Unknown tool: {name}"
