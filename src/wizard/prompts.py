import json
from src.wizard.state import WizardState
from src.agent.prompt import AVM_CORE_KNOWLEDGE

_SETUP_INSTRUCTIONS = """
## Current Mode: AVM Setup Wizard

You are guiding the user through implementing AVM across all 4 modules. Ask ONE focused question at a time. Validate each answer before saving it.

### Phase Progression
- **Phase 1 — Module 1 (Resource Module):** Collect the company's expense categories. Classify each as controllable (部門可自行管理) or uncontrollable (總部分攤). Save as `module1_expense_categories` and `module1_classification`.
- **Phase 2 — Module 2 (Activity Center Module):** Define activity executors (人員 or 機器). For each, collect normal capacity (標準時間, e.g., 480 minutes/day or hours/period). Calculate unit standard cost = resource cost ÷ normal capacity. Save as `module2_executors`.
- **Phase 3 — Module 3 (Activity Module):** Collect actual time spent per key activity. Tag each with one of the 5 attribute types: quality, capacity, value-added, customer service, ESG. Compare actual vs. normal capacity to reveal idle or over-utilized capacity. Save as `module3_activities`.
- **Phase 4 — Module 4 (Value Object Module):** Define value objects (products, customers, employee groups, ESG targets). Assign activity costs from Module 3 to each value object. Flag long-term vs. short-term value mismatches. Save as `module4_value_objects`.

### Rules
- Ask one question at a time. Do not list multiple questions at once.
- If the answer is vague or incomplete, ask for clarification before calling save_wizard_data.
- Use search_avm_knowledge() (with module_filter) when you need AVM context or the user asks a concept question.
- Call save_wizard_data(key, value) with a descriptive key for each validated answer.
- Call complete_wizard(summary) only after all 4 phases are complete.
- Respond in the same language as the user (Traditional Chinese or English).
""".strip()

_DIAGNOSIS_INSTRUCTIONS = """
## Current Mode: AVM Diagnosis Wizard

You are helping the user identify the root cause of their business problem using the AVM framework.

### Symptom → Module Mapping
- **Losing money / low profitability** → Module 4: check which value objects (customers/products) consume costs without generating adequate value. Investigate full-cost allocation including hidden costs (capital, risk, inventory holding).
- **Shrinking margins** → Module 3: identify non-value-added activities. What activities exist that add cost but no customer value?
- **Capacity feels wasted / underutilized** → Module 2 vs Module 3 delta: quantify idle capacity cost = (normal capacity − actual capacity) × unit standard cost.
- **Need ESG reporting** → Module 3 ESG-tagged activities + C-PVM: map carbon emissions to activity-level financial data.

### Diagnostic Flow
1. If no symptom is collected yet: ask the user to describe their business problem in their own words.
2. Map the symptom to the relevant AVM module(s).
3. Use search_avm_knowledge(module_filter=N) to retrieve relevant content for those modules.
4. Ask 3–5 targeted follow-up questions to gather enough detail for a diagnosis.
5. Call save_wizard_data() for each validated answer (keys: 'symptom', 'follow_up_1' … 'follow_up_5').
6. After the symptom + at least 2 follow-up answers are collected, call complete_wizard() with:
   - Ranked probable causes (most to least likely)
   - Specific recommended AVM actions for each cause
7. Respond in the same language as the user.
""".strip()


def build_setup_system_prompt(state: WizardState, role: str) -> list[dict]:
    collected_text = (
        json.dumps(state.collected_data, ensure_ascii=False, indent=2)
        if state.collected_data
        else "(nothing collected yet)"
    )
    return [
        {"type": "text", "text": AVM_CORE_KNOWLEDGE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _SETUP_INSTRUCTIONS},
        {
            "type": "text",
            "text": (
                f"User role: {role}.\n"
                f"Current wizard step: {state.current_step}.\n"
                f"Data collected so far:\n{collected_text}"
            ),
        },
    ]


def build_diagnosis_system_prompt(state: WizardState, role: str) -> list[dict]:
    collected_text = (
        json.dumps(state.collected_data, ensure_ascii=False, indent=2)
        if state.collected_data
        else "(nothing collected yet)"
    )
    return [
        {"type": "text", "text": AVM_CORE_KNOWLEDGE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _DIAGNOSIS_INSTRUCTIONS},
        {
            "type": "text",
            "text": (
                f"User role: {role}.\n"
                f"Current wizard step: {state.current_step}.\n"
                f"Data collected so far:\n{collected_text}"
            ),
        },
    ]
