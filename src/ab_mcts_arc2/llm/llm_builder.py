from ab_mcts_arc2.llm.llm_interface import Model
from ab_mcts_arc2.llm.claude_api import PRICING as CLAUDE_PRICING
from ab_mcts_arc2.llm.claude_api import ClaudeBedrockAPIModel
from ab_mcts_arc2.llm.gemini_api import PRICING as GEMINI_PRICING
from ab_mcts_arc2.llm.gemini_api import GeminiAPIModel
from ab_mcts_arc2.llm.openai_api import PRICING as OPENAI_PRICING
from ab_mcts_arc2.llm.openai_api import OpenAIAPIModel
from ab_mcts_arc2.llm.vllm_api import VLLMAPIModel


def build_model(model_name: str) -> Model:
    # vLLMモデルの場合 (vllm_ プレフィックスを持つ)
    if model_name.startswith("vllm_"):
        # "vllm_" プレフィックスを除去して実際のモデル名を取得
        actual_model_name = model_name[5:]  # "vllm_microsoft/Phi-4-mini-reasoning" -> "microsoft/Phi-4-mini-reasoning"
        return VLLMAPIModel(actual_model_name)
    elif model_name in CLAUDE_PRICING:
        model_cls = ClaudeBedrockAPIModel
    elif model_name in GEMINI_PRICING:
        model_cls = GeminiAPIModel
    elif model_name in OPENAI_PRICING:
        model_cls = OpenAIAPIModel
    else:
        raise ValueError(f"Unsupported model {model_name}")

    model = model_cls(model_name)
    return model


def call_llm(
    model_name: str, model_temp: float, messages: list[dict]
) -> tuple[str, float]:
    model = build_model(model_name)
    return model.generate(messages, model_temp)
