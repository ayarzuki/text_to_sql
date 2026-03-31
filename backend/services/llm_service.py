import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": 0.1,
                        },
                    )

                    # Handle non-200 responses with specific error detection
                    if response.status_code != 200:
                        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                        error_code = body.get("error", {}).get("code", "")
                        error_msg = body.get("error", {}).get("message", "")

                        # 1113 = insufficient balance — don't retry
                        if error_code == "1113":
                            raise ValueError(f"GLM API insufficient balance: {error_msg}. Please top up at https://open.bigmodel.cn")

                        # 1211 = model not found — don't retry
                        if error_code == "1211":
                            raise ValueError(f"GLM model '{self.model}' not found: {error_msg}")

                        # 429 = rate limit — retry with backoff
                        if response.status_code == 429:
                            wait = 3 * (attempt + 1)
                            logger.warning("Rate limited (429), retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                            await asyncio.sleep(wait)
                            last_error = Exception(f"Rate limited: {error_msg}")
                            continue

                        # Other errors — raise immediately
                        response.raise_for_status()

                    data = response.json()

                content = data["choices"][0]["message"]["content"]
                logger.info("LLM response length: %d chars", len(content))
                return content
            except (ValueError, httpx.HTTPStatusError):
                raise
            except httpx.RequestError as e:
                last_error = e
                logger.warning("Request error: %s, retrying (attempt %d/%d)", e, attempt + 1, max_retries)
                await asyncio.sleep(2)
                continue

        raise last_error or Exception("Max retries exceeded")
