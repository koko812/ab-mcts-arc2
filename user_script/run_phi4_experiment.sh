#!/bin/bash
# Phi-4実験実行スクリプト
#
# 使い方:
#   bash user_script/run_phi4_experiment.sh [TASK_ID] [MAX_NODES]
#
# 例:
#   bash user_script/run_phi4_experiment.sh 0934a4d8 100
#   bash user_script/run_phi4_experiment.sh 135a2760 50

set -e

# パラメータ
TASK_ID=${1:-0934a4d8}
MAX_NODES=${2:-100}
PORT=8001

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Phi-4 実験実行"
echo "=========================================="
echo "Task ID: $TASK_ID"
echo "Max Nodes: $MAX_NODES"
echo "vLLM Port: $PORT"
echo "=========================================="
echo ""

# 環境変数を設定
echo "環境変数を設定中..."
source user_script/setup_env.sh $PORT

echo ""
echo "vLLMサーバーが起動しているか確認してください:"
echo "  curl http://localhost:$PORT/v1/models"
echo ""

# 確認
read -p "vLLMサーバーは起動していますか？ (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "まずvLLMサーバーを起動してください:"
    echo "  cd vllm_serving"
    echo "  uv run vllm serve microsoft/Phi-4-mini-reasoning --port $PORT --trust-remote-code --max-model-len 32768"
    exit 1
fi

echo ""
echo "実験を開始します..."
echo ""

# 実験実行
cd experiments/arc2
TASK_ID=$TASK_ID uv run python run.py \
    --config-name=config_phi4 \
    task_id=$TASK_ID \
    max_num_nodes=$MAX_NODES \
    hydra.run.dir=../../outputs/arc2/phi4_${TASK_ID}_$(date +%Y%m%d_%H%M%S)

echo ""
echo "=========================================="
echo "実験完了"
echo "=========================================="
