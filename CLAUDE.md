# Claude開発ログ

このファイルは、Claudeとの対話を通じて行われた開発作業の記録です。

## 開発セッション: 2025-10-06

### セッション概要
HuggingFaceモデルをvLLM経由で使用できるようにする機能を追加

### ユーザーからの指示

1. **ブランチ作成**
   - `claude`ブランチを作成して、そこで開発を進める

2. **vLLM統合の要求**
   - 現在のリポジトリはOpenAI APIのみ対応
   - HuggingFaceのモデルに対しても、vLLMで使えるようにしたい

3. **複数モデルの組み合わせに関する質問**
   - 複数モデルを組み合わせて使用できるはずだが、そのコードの場所を確認
   - 回答: `experiments/arc2/run.py`で実装されており、TreeQuestライブラリが複数モデルを管理

4. **変更履歴のまとめ**
   - 編集内容をCHANGELOG.mdにまとめる
   - 日本語で書き直し、編集日時をタイトルの下に記載

5. **開発ログの作成**
   - 今までの指示からCLAUDE.mdを作成

### 実装内容

#### 1. vLLM APIモデルクラスの作成
- **ファイル**: `src/ab_mcts_arc2/llm/vllm_api.py`
- **内容**:
  - `VLLMAPIModel`クラスを実装
  - OpenAI互換のvLLM APIサーバーと通信
  - 環境変数`VLLM_BASE_URL`と`VLLM_API_KEY`で設定
  - リトライロジックとエラーハンドリングを実装
  - コスト追跡機能（ローカルデプロイメントではデフォルトで$0）

#### 2. LLMビルダーの更新
- **ファイル**: `src/ab_mcts_arc2/llm/llm_builder.py`
- **変更内容**:
  - `VLLMAPIModel`と`VLLM_PRICING`のインポートを追加
  - `build_model()`関数を修正し、`vllm_`プレフィックスを持つモデル名を処理
  - プレフィックスを除去して実際のモデル名を取得し、`VLLMAPIModel`にルーティング

#### 3. 依存関係の追加
- **ファイル**: `pyproject.toml`
- **変更内容**:
  - `openai>=1.12.0`を明示的な依存関係として追加
  - vLLMのOpenAI互換クライアント用

#### 4. ドキュメント作成
- **ファイル**: `docs/vllm_setup.md`
- **内容**:
  - vLLMのセットアップ手順（日本語）
  - サーバーの起動方法
  - 環境変数の設定方法
  - config.yamlでの使用例
  - サポートされているモデルのリスト
  - トラブルシューティングガイド

#### 5. 変更履歴の作成
- **ファイル**: `CHANGELOG.md`
- **内容**:
  - 日本語で変更内容を記録
  - 編集日時を含む
  - 追加・変更・技術詳細・使用例のセクション

### 技術的な決定事項

1. **命名規則**: vLLMモデルには`vllm_`プレフィックスを使用
   - 例: `vllm_Qwen/Qwen2.5-7B-Instruct`
   - これにより、モデル名からvLLMモデルであることを識別可能

2. **OpenAI互換API**: vLLMのOpenAI互換APIを活用
   - 既存の`openai`ライブラリを再利用
   - コードの一貫性を保つ

3. **環境変数による設定**: 柔軟性を確保
   - `VLLM_BASE_URL`: vLLMサーバーのURL（デフォルト: `http://localhost:8000/v1`）
   - `VLLM_API_KEY`: 認証キー（デフォルト: `EMPTY`）

4. **既存フレームワークとの互換性**:
   - Multi-LLM AB-MCTSフレームワークと完全に互換
   - 他のモデルタイプ（OpenAI、Claude、Gemini）と混在可能

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

```bash
# vLLMサーバーの起動
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000

# 環境変数の設定
export VLLM_BASE_URL="http://localhost:8000/v1"
```

### 成果物
- 新規ファイル:
  - `src/ab_mcts_arc2/llm/vllm_api.py`
  - `docs/vllm_setup.md`
  - `CHANGELOG.md`
  - `CLAUDE.md`（このファイル）

- 変更ファイル:
  - `src/ab_mcts_arc2/llm/llm_builder.py`
  - `pyproject.toml`

### 次のステップ（推奨）
1. `uv sync`を実行して依存関係を更新
2. vLLMサーバーを起動してテスト
3. 実際のARC-AGI-2問題で動作確認
4. 必要に応じてPRICINGを調整（有料エンドポイントを使用する場合）
