from typing import Optional
import chainlit as cl
from src.config import (
    ANTHROPIC_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    VOYAGE_API_KEY,
)
from src.auth.users import authenticate
from src.rag.embedder import create_embedder
from src.rag.store import create_vector_store
from src.agent.client import AVMAgentClient

_pinecone_index = create_vector_store(PINECONE_API_KEY, PINECONE_INDEX_NAME)
_embedder = create_embedder(VOYAGE_API_KEY)


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    user = authenticate(username, password)
    if user:
        return cl.User(
            identifier=username,
            metadata={"role": user["role"], "group": user["group"]},
        )
    return None


@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    role = user.metadata.get("role", "analyst") if user else "analyst"
    cl.user_session.set("role", role)
    cl.user_session.set("history", [])
    cl.user_session.set(
        "agent",
        AVMAgentClient(
            api_key=ANTHROPIC_API_KEY,
            pinecone_index=_pinecone_index,
            embedder=_embedder,
        ),
    )


@cl.on_message
async def on_message(message: cl.Message):
    role: str = cl.user_session.get("role", "analyst")
    history: list = cl.user_session.get("history", [])
    agent: AVMAgentClient = cl.user_session.get("agent")

    history.append({"role": "user", "content": message.content})

    response_msg = cl.Message(content="Thinking...")
    await response_msg.send()

    response_text = agent.get_response(history=history, role=role)

    response_msg.content = response_text
    await response_msg.update()

    history.append({"role": "assistant", "content": response_text})
    cl.user_session.set("history", history)
