import anthropic
from src.wizard.state import WizardState
from src.wizard.tools import WIZARD_TOOLS, dispatch_wizard_tool
from src.wizard.prompts import build_setup_system_prompt, build_diagnosis_system_prompt
from src.rag.retriever import retrieve_chunks

_SETUP_INTRO_EN = (
    "Welcome to the **AVM Setup Wizard**!\n\n"
    "I'll guide you through implementing Activity Value Management across all 4 modules:\n"
    "1. **Module 1 — Resource Module**: classify your expense categories\n"
    "2. **Module 2 — Activity Center Module**: define executors and standard capacity\n"
    "3. **Module 3 — Activity Module**: record actual activities and tag attributes\n"
    "4. **Module 4 — Value Object Module**: assign costs to products, customers, and more\n\n"
    "Let's start with **Module 1**. Please list your company's main expense categories "
    "(e.g., salaries, depreciation, utilities, rent, materials). Don't worry about being "
    "exhaustive — we'll refine as we go."
)

_SETUP_INTRO_ZH = (
    "歡迎使用 **AVM 設置精靈**！\n\n"
    "我將引導您完成作業價值管理的四個模組實施：\n"
    "1. **模組一 — 資源模組**：分類您的費用項目\n"
    "2. **模組二 — 作業中心模組**：定義執行者和標準產能\n"
    "3. **模組三 — 作業模組**：記錄實際作業並標記屬性\n"
    "4. **模組四 — 價值標的模組**：將成本分配給產品、客戶等\n\n"
    "我們從**模組一**開始。請列出貴公司的主要費用項目（例如：薪資、折舊、水電費、租金、材料費）。"
    "不必列舉完整，我們可以逐步補充。"
)

_DIAGNOSIS_INTRO_EN = (
    "Welcome to the **AVM Diagnosis Wizard**.\n\n"
    "Please describe the business problem you're experiencing. "
    "For example: declining profitability, shrinking margins, wasted capacity, or needing ESG reporting. "
    "The more specific you are, the better I can pinpoint the root cause."
)

_DIAGNOSIS_INTRO_ZH = (
    "歡迎使用 **AVM 診斷精靈**。\n\n"
    "請描述您目前遇到的業務問題，例如：利潤下降、毛利萎縮、產能浪費，或需要ESG報告。"
    "描述越具體，我越能準確找出根本原因。"
)


class WizardEngine:
    def __init__(self, api_key: str, pinecone_index, embedder):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.pinecone_index = pinecone_index
        self.embedder = embedder

    def start(self, wizard_type: str, language: str = "en") -> tuple[WizardState, str]:
        state = WizardState(wizard_type=wizard_type)
        is_zh = language == "zh-TW"
        if wizard_type == "setup":
            intro = _SETUP_INTRO_ZH if is_zh else _SETUP_INTRO_EN
        else:
            intro = _DIAGNOSIS_INTRO_ZH if is_zh else _DIAGNOSIS_INTRO_EN
        return state, intro

    def step(self, state: WizardState, history: list, role: str) -> tuple[WizardState, str]:
        if state.wizard_type == "setup":
            system = build_setup_system_prompt(state, role)
        else:
            system = build_diagnosis_system_prompt(state, role)

        messages = list(history)

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=WIZARD_TOOLS,
            )

            if response.stop_reason == "end_turn":
                text = next(
                    (b.text for b in response.content if b.type == "text"), ""
                )
                return state, text

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_wizard_tool(
                            block.name,
                            block.input,
                            state,
                            self._retriever,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

    def _retriever(self, query: str, module_filter=None) -> list[str]:
        return retrieve_chunks(
            self.pinecone_index,
            self.embedder,
            query,
            module_filter=module_filter,
        )
