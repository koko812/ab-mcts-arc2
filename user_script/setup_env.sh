#!/bin/bash
# vLLMクライアント用の環境変数設定スクリプト

# 使い方: source user_script/setup_env.sh [PORT]
# 例: source user_script/setup_env.sh 8001

PORT=${1:-8001}  # デフォルトは8001（8000は他ユーザーが使用中のため）

export VLLM_BASE_URL="http://localhost:${PORT}/v1"
export VLLM_API_KEY="EMPTY"
export VLLM_MAX_TOKENS="16384"  # 入力を考慮して max-model-len の半分程度に設定
export VLLM_TOP_P="0.95"

echo "=========================================="
echo "vLLM環境変数を設定しました"
echo "=========================================="
echo "VLLM_BASE_URL: $VLLM_BASE_URL"
echo "VLLM_API_KEY: $VLLM_API_KEY"
echo "VLLM_MAX_TOKENS: $VLLM_MAX_TOKENS"
echo "VLLM_TOP_P: $VLLM_TOP_P"
echo "=========================================="
