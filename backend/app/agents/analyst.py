"""Analyst operator — sandboxed code execution for research computations.

The Planner sets ``requires_computation=True`` when the question needs
statistical calculations, power/sample-size estimates, formula evaluation, or
data analysis. The Analyst executes LLM-generated Python in a restricted
namespace with:
  - An AST import whitelist (math, statistics, numpy, pandas, scipy, …)
  - Forbidden builtins stripped (open, exec, eval, __import__, compile, …)
  - A per-thread timeout (default 8 s)
  - stdout/stderr capped at 8 KB
"""
from __future__ import annotations

import ast
import contextlib
import io
import threading
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseOperator
from app.core.logging import get_logger

logger = get_logger("noesis.analyst")

_ALLOWED_IMPORTS = {
    "math", "statistics", "random", "datetime", "json", "re", "string",
    "itertools", "functools", "collections", "decimal", "fractions",
    "numpy", "pandas", "scipy", "sklearn", "matplotlib",
}
_FORBIDDEN_BUILTINS = {
    "open", "exec", "eval", "__import__", "compile",
    "input", "breakpoint", "exit", "quit",
}
_TIMEOUT_S = 8
_MAX_OUT = 8_192

_SYSTEM = """You are the Analyst operator inside Noesis, a research intelligence OS.
Write a short, self-contained Python script that answers the computational part of the user's query.
Rules:
- Use only: math, statistics, numpy, pandas, scipy
- Do NOT use: open(), exec(), eval(), network calls, file I/O
- Print the result clearly to stdout
- Keep the script under 80 lines
Output ONLY the Python code — no markdown fences, no explanation."""


def _check_ast(code: str) -> str | None:
    """Return an error message if the code violates the whitelist, else None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name.split(".")[0] for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module.split(".")[0]] if node.module else []
            )
            for name in names:
                if name not in _ALLOWED_IMPORTS:
                    return f"Import '{name}' is not allowed"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "Dunder attribute access is not allowed"
    return None


def _run_sandboxed(code: str) -> dict[str, str]:
    safe_builtins = {k: v for k, v in __builtins__.items()
                     if k not in _FORBIDDEN_BUILTINS}  # type: ignore[attr-defined]
    globs = {"__builtins__": safe_builtins}
    stdout_buf = io.StringIO()
    result: dict[str, str] = {"output": "", "error": ""}

    def _target() -> None:
        try:
            with contextlib.redirect_stdout(stdout_buf):
                exec(code, globs)  # noqa: S102
        except Exception as exc:
            result["error"] = str(exc)[:2048]

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout=_TIMEOUT_S)
    if thread.is_alive():
        result["error"] = f"Execution timed out after {_TIMEOUT_S}s"
    else:
        result["output"] = stdout_buf.getvalue()[:_MAX_OUT]
    return result


class AnalystOperator(BaseOperator):
    name = "analyst"

    async def _execute(self, state: dict[str, Any]) -> dict[str, Any]:
        from app.agents._llm import get_llm
        import asyncio

        stage_cb = state.get("stage_callback")
        if stage_cb:
            await stage_cb("analyzing", {})

        question = state["question"]
        dossier_summary = "\n".join(
            f"- {d.get('title', '')}" for d in (state.get("dossier") or [])[:5]
        )
        prompt = (
            f"Research question: {question}\n\n"
            f"Relevant context:\n{dossier_summary}\n\n"
            "Write the Python code for the computational analysis."
        )
        llm = get_llm(temperature=0.1)
        messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]

        try:
            response = await llm.ainvoke(messages)
            code = response.content.strip()
            if code.startswith("```"):
                code = code.split("```")[1]
                if code.startswith("python"):
                    code = code[6:]
                code = code.strip()
        except Exception as exc:
            return {"code_output": "", "code_error": f"LLM call failed: {exc}"}

        err = _check_ast(code)
        if err:
            return {"code_output": "", "code_error": f"Code validation failed: {err}"}

        exec_result = await asyncio.to_thread(_run_sandboxed, code)
        return {
            "code_output": exec_result["output"],
            "code_error": exec_result["error"],
        }
