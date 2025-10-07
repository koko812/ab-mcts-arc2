#!/bin/bash
# vLLMクライアント用の環境変数設定スクリプト（デバッグ版）

# 使い方: source user_script/setup_env_debug.sh [PORT]
# 例: source user_script/setup_env_debug.sh 8001

PORT=${1:-8001}  # デフォルトは8001（8000は他ユーザーが使用中のため）

export VLLM_BASE_URL="http://localhost:${PORT}/v1"
export VLLM_API_KEY="EMPTY"
export VLLM_MAX_TOKENS="100"  # デバッグ用に短く
export VLLM_TOP_P="0.95"

echo "=========================================="
echo "vLLM環境変数を設定しました（デバッグ版）"
echo "=========================================="
echo "VLLM_BASE_URL: $VLLM_BASE_URL"
echo "VLLM_API_KEY: $VLLM_API_KEY"
echo "VLLM_MAX_TOKENS: $VLLM_MAX_TOKENS (デバッグ用)"
echo "VLLM_TOP_P: $VLLM_TOP_P"
echo "=========================================="
