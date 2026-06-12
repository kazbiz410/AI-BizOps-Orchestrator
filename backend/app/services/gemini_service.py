from __future__ import annotations

import json

import httpx

from app.core.config import settings


class GeminiService:
    def generate_json(self, *, system_instruction: str, payload: dict) -> dict | None:
        if not settings.gemini_api_key:
            return None

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        body = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(payload, ensure_ascii=False)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json",
            },
        }

        try:
            response = httpx.post(url, json=body, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception:
            return None
