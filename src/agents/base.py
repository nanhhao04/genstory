"""Shared abstractions for story agents."""

from __future__ import annotations

import datetime
import json
import os
import re
from abc import ABC
from typing import Any

from src.core.llm import llm

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))


class BaseStoryAgent(ABC):
    """Common LLM plumbing used by all story agents."""

    name = "base_agent"

    async def call_text(self, system: str, user: str, log_name: str) -> str:
        prompt = f"{system}\n\n{user}"
        response = await llm.generate_content_async(
            prompt, agent_name=self.name, task_name=log_name
        )
        text = response.text
        self._log_exchange(log_name, prompt, text)
        return text

    async def call_json(
        self, system: str, user: str, log_name: str, context: str
    ) -> dict[str, Any]:
        raw = await self.call_text(system, user, log_name=log_name)
        try:
            return self.parse_json(raw, context=context)
        except ValueError as exc:
            repair_system = "You repair malformed JSON. Return valid JSON only and preserve the intended schema."
            repair_user = f"Context: {context}\nError: {exc}\n\nText to repair:\n{raw}"
            repaired = await self.call_text(
                repair_system,
                repair_user,
                log_name=f"{log_name}_repair",
            )
            return self.parse_json(repaired, context=f"{context}_repaired")

    def parse_json(self, raw: str, context: str = "") -> dict[str, Any]:
        clean = re.sub(r"```(?:json)?\s*", "", str(raw)).strip().rstrip("`").strip()
        if not (clean.startswith("{") and clean.endswith("}")):
            match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if match:
                clean = match.group(1)

        try:
            return json.loads(clean)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON parse failed [{context}]: {exc}") from exc

    def dump_json(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _log_exchange(self, filename: str, prompt: str, response: str) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, f"{filename}.json")
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": self.name,
            "prompt": prompt,
            "response": response,
        }

        data = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    if not isinstance(data, list):
                        data = [data]
            except Exception:
                data = []

        data.append(entry)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
