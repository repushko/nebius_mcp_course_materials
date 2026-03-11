import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


async def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning("Timeout on attempt %d, retrying in %ds: %s", attempt + 1, wait, e)
            await asyncio.sleep(wait)
