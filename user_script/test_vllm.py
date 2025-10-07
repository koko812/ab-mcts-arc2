#!/usr/bin/env python3
"""
vLLM統合のテストスクリプト

使い方:
1. vLLMサーバーを起動
   bash user_script/start_vllm_phi4.sh 2

2. 環境変数を設定
   export VLLM_BASE_URL="http://localhost:8000/v1"
   export VLLM_API_KEY="EMPTY"

3. このスクリプトを実行
   uv run python user_script/test_vllm.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ab_mcts_arc2.llm.llm_builder import build_model, call_llm


def test_vllm_direct():
    """VLLMAPIModelを直接テスト"""
    print("=" * 60)
    print("Test 1: VLLMAPIModel 直接テスト")
    print("=" * 60)

    # 環境変数の確認
    vllm_base_url = os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    vllm_api_key = os.environ.get("VLLM_API_KEY", "EMPTY")

    print(f"VLLM_BASE_URL: {vllm_base_url}")
    print(f"VLLM_API_KEY: {vllm_api_key}")
    print()

    # モデルを構築
    model_name = "vllm_microsoft/Phi-4-mini-reasoning"
    print(f"モデル名: {model_name}")

    try:
        model = build_model(model_name)
        print(f"✓ モデルの構築成功: {model.__class__.__name__}")
        print(f"  実際のモデル名: {model.model_name}")
        print()
    except Exception as e:
        print(f"✗ モデルの構築失敗: {e}")
        return False

    # 簡単なテストメッセージ
    messages = [
        {"role": "user", "content": "Hello! Please respond with a short greeting."}
    ]

    print("リクエスト送信中...")
    try:
        response, cost = model.generate(messages, temperature=0.6)
        print(f"✓ レスポンス受信成功")
        print(f"  レスポンス: {response[:200]}...")  # 最初の200文字
        print(f"  コスト: ${cost:.6f}")
        print()
        return True
    except Exception as e:
        print(f"✗ レスポンス受信失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vllm_via_call_llm():
    """call_llm関数経由でテスト"""
    print("=" * 60)
    print("Test 2: call_llm 関数経由テスト")
    print("=" * 60)

    model_name = "vllm_microsoft/Phi-4-mini-reasoning"
    temperature = 0.6

    messages = [
        {"role": "user", "content": "What is 2 + 2? Answer briefly."}
    ]

    print(f"モデル名: {model_name}")
    print(f"温度: {temperature}")
    print()

    print("リクエスト送信中...")
    try:
        response, cost = call_llm(model_name, temperature, messages)
        print(f"✓ レスポンス受信成功")
        print(f"  レスポンス: {response}")
        print(f"  コスト: ${cost:.6f}")
        print()
        return True
    except Exception as e:
        print(f"✗ レスポンス受信失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("\n" + "=" * 60)
    print("vLLM統合テスト")
    print("=" * 60)
    print()

    # 環境変数のチェック
    if "VLLM_BASE_URL" not in os.environ:
        print("⚠ Warning: VLLM_BASE_URL が設定されていません")
        print("  デフォルト値 http://localhost:8000/v1 を使用します")
        print()

    # テスト実行
    results = []

    # Test 1
    results.append(test_vllm_direct())

    # Test 2
    results.append(test_vllm_via_call_llm())

    # 結果サマリー
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"Test 1 (VLLMAPIModel直接): {'✓ PASS' if results[0] else '✗ FAIL'}")
    print(f"Test 2 (call_llm経由): {'✓ PASS' if results[1] else '✗ FAIL'}")
    print()

    if all(results):
        print("✓ 全てのテストが成功しました！")
        print()
        print("次のステップ:")
        print("  1. config_phi4.yaml を使って実験を実行")
        print("     cd experiments/arc2")
        print("     python run.py --config-name=config_phi4 task_id=0")
        return 0
    else:
        print("✗ いくつかのテストが失敗しました")
        print()
        print("トラブルシューティング:")
        print("  1. vLLMサーバーが起動しているか確認")
        print("     curl http://localhost:8000/v1/models")
        print("  2. 環境変数が設定されているか確認")
        print("     echo $VLLM_BASE_URL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
