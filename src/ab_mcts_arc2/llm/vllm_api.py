import logging
import os
from typing import Optional

from openai import OpenAI
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    stop_never,
    wait_exponential,
)

from ab_mcts_arc2.llm.llm_interface import Model

# Pricing for vLLM is typically local/free, but we define a structure for consistency
# Users can override these values if they're using a paid vLLM endpoint
PRICING = {
    # Default pricing (free for local deployment)
    "default": {
        "prompt_tokens": 0.0,
        "completion_tokens": 0.0,
    },
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def will_retry_generate_failure(e: BaseException) -> bool:
    """Retry logic for vLLM API errors."""
    if hasattr(e, "status_code"):
        status_code = int(e.status_code)
        if status_code in (400, 429, 500, 502, 503, 504):
            print(f"Hit a vLLM API error with status code {status_code}, retrying...")
            return True
        else:
            return False
    else:
        return False


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.INFO),
    stop=(
        stop_after_attempt(int(os.environ["VLLM_MAX_RETRY"]))
        if os.environ.get("VLLM_MAX_RETRY") is not None
        else stop_never
    ),
    retry=retry_if_exception(will_retry_generate_failure)
    | retry_if_exception_type(TypeError),
)
def try_generate(api_model: "VLLMAPIModel", messages, temperature, request_samples=1):
    """Try to generate a response from vLLM with retry logic."""
    response = api_model.client.chat.completions.create(
        messages=messages,
        model=api_model.model,
        n=request_samples,
        temperature=temperature,
    )

    if response.choices is None:
        raise TypeError("Received None response from vLLM API")

    if response.usage is None:
        raise TypeError("Received None usage from vLLM API")

    return response


class VLLMAPIModel(Model):
    """Model class for HuggingFace models served via vLLM.

    vLLM provides an OpenAI-compatible API, so we use the OpenAI client.

    Usage:
        Set VLLM_BASE_URL environment variable to your vLLM server URL.
        Example: export VLLM_BASE_URL="http://localhost:8000/v1"

        Set VLLM_API_KEY if your vLLM server requires authentication.
        Example: export VLLM_API_KEY="your-api-key"
    """

    def __init__(
        self,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize vLLM API model.

        Args:
            model: Model name as recognized by the vLLM server
            base_url: vLLM server URL (defaults to VLLM_BASE_URL env var)
            api_key: API key for authentication (defaults to VLLM_API_KEY env var or "EMPTY")
        """
        self.model = self.model_name = model

        # Get base URL from parameter or environment variable
        base_url = base_url or os.environ.get(
            "VLLM_BASE_URL", "http://localhost:8000/v1"
        )

        # Get API key from parameter or environment variable
        # vLLM servers often don't require authentication, so we default to "EMPTY"
        api_key = api_key or os.environ.get("VLLM_API_KEY", "EMPTY")

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        logger.info(f"Initialized vLLM client for model {model} at {base_url}")

    def generate(
        self, messages: list[dict[str, str]], temperature: float = 0.6
    ) -> tuple[str, float]:
        """Generate a response using the vLLM API.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Sampling temperature

        Returns:
            Tuple of (response_text, cost)
        """
        chat_completion = try_generate(self, messages, temperature)
        usage_data = chat_completion.usage.model_dump()

        # Calculate cost (typically 0 for local vLLM deployments)
        pricing = PRICING.get(self.model_name, PRICING["default"])
        cost = (
            pricing["prompt_tokens"] * usage_data["prompt_tokens"]
            + pricing["completion_tokens"] * usage_data["completion_tokens"]
        )

        return chat_completion.choices[0].message.content, cost
