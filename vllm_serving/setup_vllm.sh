#!/bin/bash
# vLLM serving環境のセットアップスクリプト

set -e

echo "=========================================="
echo "vLLM Serving 環境セットアップ"
echo "=========================================="

# vllm_servingディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "作業ディレクトリ: $(pwd)"
echo ""

# uvがインストールされているか確認
if ! command -v uv &> /dev/null; then
    echo "Error: uv がインストールされていません"
    echo "インストール方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv が見つかりました"
echo ""

# pyproject.tomlが存在するか確認
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml が見つかりません"
    echo "pyproject.toml がリポジトリに含まれているはずです"
    exit 1
fi

echo "✓ pyproject.toml が見つかりました"
echo ""

# vLLMをインストール
echo "vLLMをインストール中..."
uv sync

echo ""
echo "✓ vLLMのインストールが完了しました"
echo ""

echo "=========================================="
echo "セットアップ完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. vLLMサーバーを起動:"
echo "   bash vllm_serving/start_vllm_phi4.sh [GPU数]"
echo ""
echo "=========================================="
