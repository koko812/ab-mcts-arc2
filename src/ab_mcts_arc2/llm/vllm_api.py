import json
import logging
import os

from openai import APIConnectionError, OpenAI
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

# vLLM pricing - デフォルトは$0 (ローカルデプロイメント想定)
# 有料のvLLMエンドポイントを使う場合は、ここに価格を追加してください
PRICING = {
    "default": {
        "prompt_tokens": 0.0,
        "completion_tokens": 0.0,
    }
}

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def will_retry_generate_failure(e: BaseException) -> bool:
    """vLLM API エラーのリトライ判定"""
    if hasattr(e, "status_code"):
        status_code = int(e.status_code)
        if status_code in (400, 429, 500, 502, 503, 504):
            print(f"Hit an API error with status code {status_code}, retrying...")
            return True
        else:
            return False
    else:
        return False


# The sleep durations before the retries are 1s, 2s, 4s, 8s, 8s, 8s...
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    before_sleep=before_sleep_log(logger, logging.INFO),
    stop=(
        stop_after_attempt(int(os.environ["VLLM_MAX_RETRY"]))
        if os.environ.get("VLLM_MAX_RETRY") is not None
        else stop_after_attempt(10)  # デフォルトは10回まで
    ),
    retry=retry_if_exception_type(json.JSONDecodeError)
    | retry_if_exception_type(APIConnectionError)
    | retry_if_exception(will_retry_generate_failure)
    | retry_if_exception_type(TypeError),
)
def try_generate(api_model: "VLLMAPIModel", messages, temperature, request_samples=1):
    """vLLM APIにリクエストを送信"""
    # 環境変数からサンプリングパラメータを取得
    top_p = float(os.environ.get("VLLM_TOP_P", "0.95"))

    # モデルの最大コンテキスト長（通常32768）
    max_model_len = int(os.environ.get("VLLM_MAX_MODEL_LEN", "32768"))

    # 入力プロンプトのトークン数を概算（1文字=約0.5トークンと仮定、安全マージン込み）
    prompt_text = " ".join([msg.get("content", "") for msg in messages])
    estimated_input_tokens = int(len(prompt_text) * 0.6)  # 安全側に多めに見積もる

    # 利用可能な出力トークン数を計算（安全マージン200を確保）
    available_tokens = max_model_len - estimated_input_tokens - 200

    # デフォルトのmax_tokensを取得（環境変数から、なければ16384）
    default_max_tokens = int(os.environ.get("VLLM_MAX_TOKENS", "16384"))

    # 実際に使用するmax_tokensは利用可能トークン数とデフォルトの小さい方
    max_tokens = min(available_tokens, default_max_tokens)

    # 最小値チェック（少なくとも1000トークンは確保）
    if max_tokens < 1000:
        print(f"Warning: max_tokens is very small ({max_tokens}). Input may be too long.")
        max_tokens = 1000

    response = api_model.client.chat.completions.create(
        messages=messages,
        model=api_model.model,
        n=request_samples,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )

    # If response.choices is None, raise an exception to trigger retry
    if response.choices is None:
        raise TypeError("Received None response from API")

    if response.usage is None:
        raise TypeError("Received None usage from API")

    return response


class VLLMAPIModel(Model):
    """vLLM OpenAI-compatible API client"""

    def __init__(
        self,
        model: str,
    ) -> None:
        # 環境変数からvLLMサーバーの設定を取得
        vllm_base_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
        vllm_api_key = os.environ.get("VLLM_API_KEY", "EMPTY")

        # OpenAI互換のクライアントを初期化
        self.client = OpenAI(base_url=vllm_base_url, api_key=vllm_api_key)

        self.model = self.model_name = model

        logger.info(f"Initialized vLLM model: {model} at {vllm_base_url}")

    def generate(
        self, messages: list[dict[str, str]], temperature: float = 0.6
    ) -> tuple[str, float]:
        """
        メッセージを生成し、コストを計算して返す

        Args:
            messages: チャットメッセージのリスト
            temperature: 生成時の温度パラメータ

        Returns:
            (生成されたテキスト, コスト) のタプル
        """
        chat_completion = try_generate(self, messages, temperature)
        usage_data = chat_completion.usage.model_dump()

        # コスト計算 (モデル名がPRICINGにあればそれを使用、なければdefault)
        pricing = PRICING.get(self.model_name, PRICING["default"])
        cost = (
            pricing["prompt_tokens"] * usage_data["prompt_tokens"]
            + pricing["completion_tokens"] * usage_data["completion_tokens"]
        )

        return chat_completion.choices[0].message.content, cost
