# vLLM Integration for HuggingFace Models

このドキュメントでは、vLLMを使用してHuggingFaceモデルを統合する方法を説明します。

## vLLMサーバーのセットアップ

### 1. vLLMのインストール

```bash
pip install vllm
```

### 2. vLLMサーバーの起動

HuggingFaceモデルをvLLM経由で提供するには、vLLMサーバーを起動します：

```bash
python -m vllm.entrypoints.openai.api_server \
    --model <huggingface-model-name> \
    --host 0.0.0.0 \
    --port 8000
```

例：
```bash
# Qwen2.5-7B-Instructを使用する場合
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000

# DeepSeek-R1-Distill-Qwen-7Bを使用する場合
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
    --host 0.0.0.0 \
    --port 8000
```

### 3. 環境変数の設定

vLLMサーバーのURLを環境変数として設定します：

```bash
export VLLM_BASE_URL="http://localhost:8000/v1"
```

認証が必要な場合：
```bash
export VLLM_API_KEY="your-api-key"
```

## 使い方

### config.yamlでの設定

`experiments/arc2/configs/config.yaml`にvLLMモデルを追加します：

```yaml
models:
  - name: "vllm_Qwen/Qwen2.5-7B-Instruct"
    temperature: 0.6
  - name: "vllm_deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    temperature: 0.6
  - name: "o4-mini-2025-04-16"
    temperature: 0.6
```

**重要**: モデル名の前に `vllm_` プレフィックスを付ける必要があります。

### Pythonコードでの使用例

```python
from ab_mcts_arc2.llm.llm_builder import build_model

# vLLMモデルを構築
model = build_model("vllm_Qwen/Qwen2.5-7B-Instruct")

# メッセージを生成
messages = [
    {"role": "user", "content": "Hello, how are you?"}
]
response, cost = model.generate(messages, temperature=0.6)
print(response)
```

## サポートされているモデル

vLLMは多くのHuggingFaceモデルをサポートしています。例：

- **Qwen**: `Qwen/Qwen2.5-7B-Instruct`, `Qwen/Qwen2.5-32B-Instruct`
- **DeepSeek**: `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
- **Llama**: `meta-llama/Llama-3.3-70B-Instruct`
- **Mistral**: `mistralai/Mistral-7B-Instruct-v0.3`

詳細は[vLLMドキュメント](https://docs.vllm.ai/)を参照してください。

## トラブルシューティング

### vLLMサーバーに接続できない

1. サーバーが起動していることを確認：
   ```bash
   curl http://localhost:8000/v1/models
   ```

2. `VLLM_BASE_URL`環境変数が正しく設定されていることを確認

### メモリ不足エラー

大きなモデルを使用する場合、GPUメモリが不足する可能性があります。以下のオプションを試してください：

```bash
# テンソル並列処理を使用
python -m vllm.entrypoints.openai.api_server \
    --model <model-name> \
    --tensor-parallel-size 2

# 量子化を使用
python -m vllm.entrypoints.openai.api_server \
    --model <model-name> \
    --quantization awq
```

## 価格設定

ローカルでvLLMを実行する場合、コストは通常0です。有料のvLLMエンドポイントを使用する場合は、`src/ab_mcts_arc2/llm/vllm_api.py`の`PRICING`辞書を更新してください。
