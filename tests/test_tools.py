from src.agent.tools import TOOLS, dispatch_tool

def test_tools_list_contains_search_avm_knowledge():
    names = [t["name"] for t in TOOLS]
    assert "search_avm_knowledge" in names

def test_tools_list_contains_get_user_context():
    names = [t["name"] for t in TOOLS]
    assert "get_user_context" in names

def test_search_tool_has_required_query_param():
    tool = next(t for t in TOOLS if t["name"] == "search_avm_knowledge")
    assert "query" in tool["input_schema"]["properties"]
    assert "query" in tool["input_schema"]["required"]

def test_search_tool_module_filter_is_optional():
    tool = next(t for t in TOOLS if t["name"] == "search_avm_knowledge")
    assert "module_filter" in tool["input_schema"]["properties"]
    assert "module_filter" not in tool["input_schema"].get("required", [])

def test_dispatch_search_calls_retriever():
    mock_retriever = lambda q, module_filter=None: [f"result for {q}"]
    result = dispatch_tool(
        "search_avm_knowledge",
        {"query": "idle capacity"},
        retriever=mock_retriever,
        role="analyst",
    )
    assert "result for idle capacity" in result

def test_dispatch_get_user_context_returns_role():
    result = dispatch_tool(
        "get_user_context",
        {},
        retriever=lambda q, **kw: [],
        role="manager",
    )
    assert "manager" in result

def test_dispatch_unknown_tool_returns_error_string():
    result = dispatch_tool(
        "nonexistent_tool",
        {},
        retriever=lambda q, **kw: [],
        role="analyst",
    )
    assert "Unknown tool" in result or "nonexistent_tool" in result
