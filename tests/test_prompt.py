from src.agent.prompt import build_system_prompt

def test_system_prompt_returns_list_of_blocks():
    prompt = build_system_prompt("manager")
    assert isinstance(prompt, list)
    assert len(prompt) >= 2

def test_first_block_has_cache_control():
    prompt = build_system_prompt("analyst")
    assert prompt[0]["type"] == "text"
    assert prompt[0].get("cache_control") == {"type": "ephemeral"}

def test_role_block_mentions_role():
    prompt = build_system_prompt("executive")
    role_block = prompt[-1]
    assert "executive" in role_block["text"].lower()

def test_prompt_contains_avm_core_content():
    prompt = build_system_prompt("analyst")
    full_text = " ".join(b["text"] for b in prompt)
    assert "Activity Value Management" in full_text or "AVM" in full_text
    assert "Module" in full_text

def test_cached_block_has_no_role_leakage():
    prompt_exec = build_system_prompt("executive")
    prompt_analyst = build_system_prompt("analyst")
    # The cached (first) block must be identical across roles
    assert prompt_exec[0]["text"] == prompt_analyst[0]["text"]
