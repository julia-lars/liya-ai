"""DeepSeek API client for Wenqu engine.

Uses OpenAI-compatible API format to call DeepSeek models.
"""

import json
import logging
import os
from typing import Optional

import httpx

log = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60.0


class DeepSeekClient:
    """Simple OpenAI-compatible client for DeepSeek API."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = os.environ.get("DEEPSEEK_API_URL", DEEPSEEK_API_URL)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_TIMEOUT,
        )

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request to DeepSeek.

        Args:
            prompt: User message content
            system_prompt: Optional system message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Response text content
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"DeepSeek API call failed: {e}")
            # Return a fallback response
            return json.dumps({
                "question": "请详细解释你的核心方法？",
                "question_type": "principle",
                "evaluation": "",
                "depth_score": 5,
            })

    async def close(self):
        await self.client.aclose()
