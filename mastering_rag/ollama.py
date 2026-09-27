from __future__ import annotations

import json
from typing import Any

import requests


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embed_model: str, timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.timeout = timeout

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}{path}", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Ollama request failed. Is `ollama serve` running and are the models pulled? {exc}"
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        data = self._post("/api/embed", {"model": self.embed_model, "input": texts})
        return data["embeddings"]

    def chat(self, system: str, user: str, json_mode: bool = False) -> str:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0},
        }
        if json_mode:
            payload["format"] = "json"
        return self._post("/api/chat", payload)["message"]["content"]

    def chat_json(self, system: str, user: str) -> dict[str, Any]:
        raw = self.chat(system, user, json_mode=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama returned invalid JSON: {raw}") from exc
