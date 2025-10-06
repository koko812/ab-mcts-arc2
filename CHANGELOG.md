# 変更履歴

このプロジェクトのすべての重要な変更をこのファイルに記録します。

## [未リリース]

### 編集日時: 2025-10-06

### 追加
- HuggingFaceモデル向けのvLLM統合機能
  - `src/ab_mcts_arc2/llm/vllm_api.py`に新しい`VLLMAPIModel`クラスを追加
  - vLLM経由でHuggingFaceモデルを提供する機能
  - OpenAI互換のvLLM APIエンドポイントをサポート
  - `VLLM_BASE_URL`と`VLLM_API_KEY`環境変数で設定可能
  - 指数バックオフによるリトライロジックを実装
  - コスト追跡機能（ローカルデプロイメントではデフォルトで$0）

- vLLMモデルの命名規則: `vllm_`プレフィックスを使用
  - 例: `vllm_Qwen/Qwen2.5-7B-Instruct`
  - 例: `vllm_deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`

- vLLMのセットアップと使用方法に関するドキュメント `docs/vllm_setup.md`（日本語）
  - サーバーセットアップ手順
  - 設定例
  - サポートされているモデルのリスト
  - トラブルシューティングガイド

### 変更
- `src/ab_mcts_arc2/llm/llm_builder.py`を更新
  - `VLLMAPIModel`と`VLLM_PRICING`のインポートを追加
  - `build_model()`関数を修正し、`vllm_`プレフィックスを処理
  - `vllm_`プレフィックス付きのモデルは`VLLMAPIModel`にルーティングされる

- `pyproject.toml`を更新
  - `openai>=1.12.0`を明示的な依存関係として追加（vLLM OpenAI互換クライアント用）

### 技術詳細
- vLLMモデルはvLLMのOpenAI互換APIサーバー経由で提供
- 一貫性のために同じ`OpenAI`クライアントライブラリを使用
- すべての標準パラメータをサポート（temperature、messagesなど）
- 既存のMulti-LLM AB-MCTSフレームワークと互換性あり
- `config.yaml`で他のモデルタイプ（OpenAI、Claude、Gemini）と組み合わせ可能

### 使用例
```yaml
# experiments/arc2/configs/config.yaml
models:
  - name: "vllm_Qwen/Qwen2.5-7B-Instruct"
    temperature: 0.6
  - name: "vllm_deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    temperature: 0.6
  - name: "o4-mini-2025-04-16"
    temperature: 0.6
```
