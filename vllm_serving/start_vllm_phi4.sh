#!/bin/bash
# vLLMサーバーを起動するスクリプト (microsoft/Phi-4-mini-reasoning用)
#
# ⚠️ 注意: このスクリプトは環境によっては動作しない場合があります
#
# 問題が発生する場合（特にポート競合エラー）は、以下のコマンドを直接実行してください:
#
#   cd vllm_serving
#   uv run vllm serve microsoft/Phi-4-mini-reasoning \
#       --port 8001 \
#       --tensor-parallel-size 1 \
#       --gpu-memory-utilization 0.9 \
#       --max-model-len 32768 \
#       --trust-remote-code
#
# 詳細は docs/VLLM_INTEGRATION_GUIDE.md の「トラブルシューティング」を参照してください

set -e

# vllm_servingディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# pyproject.tomlが存在するか確認
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml が見つかりません"
    echo "まず setup_vllm.sh を実行してください:"
    echo "  bash vllm_serving/setup_vllm.sh"
    exit 1
fi

MODEL="microsoft/Phi-4-mini-reasoning"
PORT=${VLLM_PORT:-8000}       # 環境変数で変更可能、デフォルトは8000
TENSOR_PARALLEL_SIZE=${1:-1}  # デフォルトは1 GPU、引数で指定可能
GPU_MEMORY_UTIL=${2:-0.9}     # デフォルトは0.9、引数で指定可能

echo "=========================================="
echo "vLLM サーバー起動"
echo "=========================================="
echo "Model: $MODEL"
echo "Port: $PORT"
echo "Tensor Parallel Size: $TENSOR_PARALLEL_SIZE"
echo "GPU Memory Utilization: $GPU_MEMORY_UTIL"
echo "=========================================="
echo ""
echo "クライアント側（別ターミナル）で環境変数を設定してください:"
echo "  export VLLM_BASE_URL=\"http://localhost:$PORT/v1\""
echo "  export VLLM_API_KEY=\"EMPTY\""
echo ""
echo "=========================================="
echo ""

# vLLMサーバーを起動
echo "モデルをロード中... (初回は数分〜数十分かかる場合があります)"
echo ""

# 新しいvLLM CLIコマンドを使用（vLLM 0.6+）
uv run vllm serve $MODEL \
    --host 0.0.0.0 \
    --port $PORT \
    --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
    --gpu-memory-utilization $GPU_MEMORY_UTIL \
    --max-model-len 32768 \
    --trust-remote-code
