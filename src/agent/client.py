import anthropic
from src.agent.prompt import build_system_prompt
from src.agent.tools import TOOLS, dispatch_tool
from src.rag.retriever import retrieve_chunks

class AVMAgentClient:
    def __init__(self, api_key: str, pinecone_index, embedder):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.pinecone_index = pinecone_index
        self.embedder = embedder

    def _retriever(self, query: str, module_filter=None) -> list[str]:
        return retrieve_chunks(
            self.pinecone_index,
            self.embedder,
            query,
            module_filter=module_filter,
        )

    def get_response(self, history: list[dict], role: str) -> str:
        system = build_system_prompt(role)
        messages = list(history)

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=TOOLS,
            )

            if response.stop_reason == "end_turn":
                return next(
                    (b.text for b in response.content if b.type == "text"),
                    "",
                )

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = dispatch_tool(
                            block.name,
                            block.input,
                            retriever=self._retriever,
                            role=role,
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
