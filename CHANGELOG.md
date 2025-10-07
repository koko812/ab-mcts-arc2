# Changelog

## [Unreleased] - 2025-10-07

### Added - vLLM Integration

vLLMサーバー経由でHuggingFaceモデルを使用できる機能を追加しました。これにより、ローカルGPU環境でPhi-4-mini-reasoningなどのオープンソースモデルをAB-MCTSに統合できます。

#### 新規ファイル

**コア実装:**
- `src/ab_mcts_arc2/llm/vllm_api.py` - VLLMAPIModelクラスの実装
  - OpenAI互換のvLLM APIサーバーと通信
  - 環境変数（VLLM_BASE_URL, VLLM_API_KEY, VLLM_MAX_TOKENS, VLLM_TOP_P）で設定
  - リトライロジックとエラーハンドリング（openai_api.pyから流用）
  - コスト追跡機能（ローカルデプロイメントではデフォルトで$0）

**vLLM Serving環境（独立環境）:**
- `vllm_serving/pyproject.toml` - vLLM専用の依存関係管理
- `vllm_serving/setup_vllm.sh` - vLLM環境セットアップスクリプト
- `vllm_serving/start_vllm_phi4.sh` - Phi-4-mini-reasoning用サーバー起動スクリプト
- `vllm_serving/USER_README.md` - vLLM環境の使用方法ガイド

**テスト・ユーティリティ:**
- `user_script/test_vllm.py` - vLLM統合テストスクリプト（通常版）
- `user_script/test_vllm_debug.py` - デバッグ用テストスクリプト（短い出力）
- `user_script/setup_env.sh` - vLLM環境変数設定スクリプト（本番用）
- `user_script/setup_env_debug.sh` - vLLM環境変数設定スクリプト（デバッグ用）
- `user_script/USER_README.md` - ユーザースクリプトの使用方法

**設定ファイル:**
- `experiments/arc2/configs/config_phi4.yaml` - Phi-4専用の実験設定

#### 変更ファイル

- `src/ab_mcts_arc2/llm/llm_builder.py`
  - `vllm_`プレフィックスを持つモデル名のルーティング追加
  - `vllm_microsoft/Phi-4-mini-reasoning` → `VLLMAPIModel("microsoft/Phi-4-mini-reasoning")`

#### 技術的な設計決定

**1. 依存関係の分離**
- vLLMサーバーは`vllm_serving/`で独立した環境として管理
- メインプロジェクトとvLLM環境の依存関係を分離（`--no-workspace`）
- メインプロジェクトはvLLMクライアント（OpenAI互換API）のみ

**2. OpenAI互換APIの活用**
- vLLMのOpenAI互換APIを活用し、既存の`openai`ライブラリを再利用
- `openai_api.py`の実装パターンを流用（約80%のコード流用）
- リトライロジック、エラーハンドリングは実績のある実装を使用

**3. 環境変数による柔軟な設定**
- `VLLM_BASE_URL`: vLLMサーバーのURL（デフォルト: `http://localhost:8000/v1`）
- `VLLM_API_KEY`: 認証キー（デフォルト: `EMPTY`）
- `VLLM_MAX_TOKENS`: 最大出力トークン数（デフォルト: `16384`）
- `VLLM_TOP_P`: Top-pサンプリング（デフォルト: `0.95`）

**4. 命名規則**
- vLLMモデルには`vllm_`プレフィックスを使用
- 例: `vllm_microsoft/Phi-4-mini-reasoning`
- これにより、モデル名からvLLMモデルであることを識別可能

#### 使用例

```bash
# 1. vLLM環境のセットアップ（初回のみ）
bash vllm_serving/setup_vllm.sh

# 2. vLLMサーバーの起動（別ターミナル）
VLLM_PORT=8001 bash vllm_serving/start_vllm_phi4.sh 1

# 3. 環境変数の設定
source user_script/setup_env.sh 8001

# 4. テスト実行
uv run python user_script/test_vllm.py

# 5. 実験実行
cd experiments/arc2
TASK_ID=0934a4d8 uv run python run.py \
    --config-name=config_phi4 \
    task_id=0934a4d8 \
    max_num_nodes=100
```

#### 動作確認済み環境

- **モデル**: microsoft/Phi-4-mini-reasoning
- **GPU**: RTX 6000 Ada × 1-4枚
- **vLLM**: 0.11.0
- **Python**: 3.11+

#### 既存フレームワークとの互換性

- Multi-LLM AB-MCTSフレームワークと完全に互換
- 他のモデルタイプ（OpenAI、Claude、Gemini）と混在可能
- TreeQuestライブラリによる探索木管理

#### 今後の拡張可能性

- 他のHuggingFaceモデルへの対応（モデル名を変えるだけ）
- 複数vLLMサーバーの同時使用
- Completions APIのサポート（Chat Completions APIが不安定な場合）

---

## 開発履歴

### セッション概要 (2025-10-07)
HuggingFaceモデルをvLLM経由でAB-MCTSに統合する機能を実装しました。

### 主な成果
✅ vLLM APIクライアントの実装完了
✅ 独立したvLLM serving環境の構築
✅ テストスクリプトとドキュメントの整備
✅ Phi-4-mini-reasoningでの動作確認成功
✅ ARC-AGI-2問題での実験実行確認
