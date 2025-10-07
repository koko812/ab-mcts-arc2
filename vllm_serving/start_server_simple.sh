#!/bin/bash
# vLLMサーバー起動スクリプト（シンプル版）
#
# これは実際に動作が確認されたコマンドです
# 使い方: bash vllm_serving/start_server_simple.sh [PORT]

set -e

cd "$(dirname "$0")"

PORT=${1:-8001}

echo "=========================================="
echo "vLLM サーバー起動（シンプル版）"
echo "=========================================="
echo "Model: microsoft/Phi-4-mini-reasoning"
echo "Port: $PORT"
echo "=========================================="
echo ""
echo "サーバーが起動したら、別のターミナルで:"
echo "  source user_script/setup_env.sh $PORT"
echo "  bash user_script/run_phi4_experiment.sh <TASK_ID> <MAX_NODES>"
echo ""
echo "=========================================="
echo ""

uv run vllm serve microsoft/Phi-4-mini-reasoning \
    --port $PORT \
    --trust-remote-code \
    --max-model-len 32768
