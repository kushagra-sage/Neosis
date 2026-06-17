"""Shared LLM factory — returns a configured ChatGroq instance."""
from __future__ import annotations

from langchain_groq import ChatGroq
from app.config import settings


def get_llm(temperature: float = 0.0) -> ChatGroq:
    api_key = settings.groq_api_key.get_secret_value()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file to use the LLM operators."
        )
    return ChatGroq(
        api_key=api_key,
        model=settings.groq_model,
        temperature=temperature,
        streaming=True,
    )
