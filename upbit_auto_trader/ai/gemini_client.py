from __future__ import annotations

import json
import os

import google.generativeai as genai

from ai.prompting import SYSTEM_PROMPT


class GeminiClient:
    def __init__(self, model_name: str):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
        self.model_name = model_name

    def analyze_candidate(self, candidate: dict, similar_patterns: list[dict]) -> str:
        if not os.getenv("GEMINI_API_KEY"):
            return json.dumps(
                {
                    "decision": "HOLD",
                    "confidence_score": 0,
                    "reason": "GEMINI_API_KEY not set",
                    "recommended_stop_loss": -2.5,
                }
            )

        prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"candidate={candidate}\n"
            f"similar_patterns={similar_patterns[:3]}"
        )
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
