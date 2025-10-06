from ab_mcts_arc2.llm.llm_interface import Model
from ab_mcts_arc2.llm.claude_api import PRICING as CLAUDE_PRICING
from ab_mcts_arc2.llm.claude_api import ClaudeBedrockAPIModel
from ab_mcts_arc2.llm.gemini_api import PRICING as GEMINI_PRICING
from ab_mcts_arc2.llm.gemini_api import GeminiAPIModel
from ab_mcts_arc2.llm.openai_api import PRICING as OPENAI_PRICING
from ab_mcts_arc2.llm.openai_api import OpenAIAPIModel
from ab_mcts_arc2.llm.vllm_api import PRICING as VLLM_PRICING
from ab_mcts_arc2.llm.vllm_api import VLLMAPIModel


def build_model(model_name: str) -> Model:
    # Check if model name starts with "vllm_" prefix for vLLM models
    if model_name.startswith("vllm_"):
        # Remove the "vllm_" prefix to get the actual model name
        actual_model_name = model_name[5:]
        model = VLLMAPIModel(actual_model_name)
    elif model_name in CLAUDE_PRICING:
        model_cls = ClaudeBedrockAPIModel
        model = model_cls(model_name)
    elif model_name in GEMINI_PRICING:
        model_cls = GeminiAPIModel
        model = model_cls(model_name)
    elif model_name in OPENAI_PRICING:
        model_cls = OpenAIAPIModel
        model = model_cls(model_name)
    else:
        raise ValueError(f"Unsupported model {model_name}")

    return model


def call_llm(
    model_name: str, model_temp: float, messages: list[dict]
) -> tuple[str, float]:
    model = build_model(model_name)
    return model.generate(messages, model_temp)
