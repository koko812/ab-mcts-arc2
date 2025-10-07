# vLLM統合ガイド

このドキュメントでは、ab-mcts-arc2にvLLMを統合するために行った具体的な実装手順を説明します。

## 目次

1. [概要](#概要)
2. [実装手順](#実装手順)
3. [ファイル構成](#ファイル構成)
4. [技術的な詳細](#技術的な詳細)
5. [トラブルシューティング](#トラブルシューティング)

## 概要

vLLM統合により、HuggingFaceのオープンソースモデル（Phi-4-mini-reasoningなど）をローカルGPU環境で実行し、AB-MCTSフレームワークに統合できるようになりました。

### 設計方針

1. **既存コードの流用**: `openai_api.py`の実装パターンを最大限活用
2. **依存関係の分離**: vLLMサーバーは独立環境で管理
3. **OpenAI互換API**: vLLMのOpenAI互換APIを活用し、同じクライアントライブラリを使用
4. **環境変数による設定**: 柔軟な設定変更が可能

## 実装手順

### ステップ1: vLLM APIクライアントの実装

**ファイル**: `src/ab_mcts_arc2/llm/vllm_api.py`

#### 1.1 基本構造の作成

`openai_api.py`をベースに、以下の要素を流用：

```python
# 流用した要素:
- リトライロジック (@retry デコレーター)
- エラーハンドリング (will_retry_generate_failure関数)
- OpenAIクライアントの使用パターン
- API呼び出しメソッド (chat.completions.create)
```

#### 1.2 変更した部分

```python
# openai_api.py との違い:

1. base_urlの設定:
   - openai_api.py: "https://api.openai.com"
   - vllm_api.py: 環境変数 VLLM_BASE_URL (デフォルト: "http://localhost:8000/v1")

2. api_keyの設定:
   - openai_api.py: os.environ["OPENAI_API_KEY"]
   - vllm_api.py: os.environ.get("VLLM_API_KEY", "EMPTY")

3. PRICINGの簡略化:
   - openai_api.py: 125行の詳細な価格表
   - vllm_api.py: 7行のシンプルな設定（ローカルはデフォルト$0）

4. 削除した機能:
   - OPENAI_REASONING_MODELS の判定
   - DeepSeek/OpenRouter の分岐処理
   - reasoning_effort パラメータ
```

#### 1.3 環境変数によるパラメータ設定

```python
def try_generate(api_model: "VLLMAPIModel", messages, temperature, request_samples=1):
    # 環境変数から取得（デフォルト値あり）
    max_tokens = int(os.environ.get("VLLM_MAX_TOKENS", "16384"))
    top_p = float(os.environ.get("VLLM_TOP_P", "0.95"))

    response = api_model.client.chat.completions.create(
        messages=messages,
        model=api_model.model,
        n=request_samples,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
```

**重要**: `max_tokens`はモデルの`max-model-len`（32768）より小さく設定する必要があります。入力トークン数を考慮して、デフォルトは半分の16384に設定。

### ステップ2: LLMビルダーの更新

**ファイル**: `src/ab_mcts_arc2/llm/llm_builder.py`

#### 2.1 インポート追加

```python
from ab_mcts_arc2.llm.vllm_api import VLLMAPIModel
```

#### 2.2 モデルルーティングの追加

```python
def build_model(model_name: str) -> Model:
    # vLLMモデルの場合 (vllm_ プレフィックスを持つ)
    if model_name.startswith("vllm_"):
        # "vllm_" プレフィックスを除去して実際のモデル名を取得
        actual_model_name = model_name[5:]  # "vllm_microsoft/Phi-4-mini-reasoning" -> "microsoft/Phi-4-mini-reasoning"
        return VLLMAPIModel(actual_model_name)
    elif model_name in CLAUDE_PRICING:
        model_cls = ClaudeBedrockAPIModel
    # ... 既存のロジック
```

**命名規則**: `vllm_`プレフィックスで識別
- 設定例: `vllm_microsoft/Phi-4-mini-reasoning`
- 実際のモデル名: `microsoft/Phi-4-mini-reasoning`

### ステップ3: vLLM Serving環境の構築

vLLMサーバーは**メインプロジェクトと分離**した独立環境として管理。

#### 3.1 ディレクトリ構成

```
vllm_serving/
├── pyproject.toml          # vLLM専用の依存関係
├── setup_vllm.sh            # セットアップスクリプト
├── start_vllm_phi4.sh       # サーバー起動スクリプト
├── USER_README.md           # 使い方ガイド
└── uv.lock                  # ロックファイル
```

#### 3.2 pyproject.toml

シンプルな設定（ビルド不要）:

```toml
[project]
name = "vllm-serving"
version = "0.1.0"
description = "vLLM serving environment"
requires-python = ">=3.10"
dependencies = [
    "vllm",  # バージョン指定なし
]
```

**重要な決定**:
- `[build-system]`セクションを削除 → ビルドエラーを回避
- バージョン指定なし → 最新版を自動取得

#### 3.3 setup_vllm.sh

```bash
#!/bin/bash
cd "$(dirname "$0")"

# pyproject.tomlが存在するか確認
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml が見つかりません"
    exit 1
fi

# vLLMをインストール
uv sync
```

**ポイント**:
- `uv init`は使わない（既にpyproject.tomlをリポジトリに含める）
- `uv sync`のみ実行

#### 3.4 start_vllm_phi4.sh

**注意**: このスクリプトは動作しない場合があります。詳細は[トラブルシューティング](#トラブルシューティング)を参照。

```bash
#!/bin/bash
cd "$(dirname "$0")"

MODEL="microsoft/Phi-4-mini-reasoning"
PORT=${VLLM_PORT:-8000}
TENSOR_PARALLEL_SIZE=${1:-1}
GPU_MEMORY_UTIL=${2:-0.9}

# 新しいvLLM CLIコマンドを使用
uv run vllm serve $MODEL \
    --host 0.0.0.0 \
    --port $PORT \
    --tensor-parallel-size $TENSOR_PARALLEL_SIZE \
    --gpu-memory-utilization $GPU_MEMORY_UTIL \
    --max-model-len 32768 \
    --trust-remote-code
```

### ステップ4: テストスクリプトの作成

**ディレクトリ**: `user_script/`

#### 4.1 test_vllm.py（通常版）

```python
# 2つのテストを実行:
# 1. VLLMAPIModelを直接テスト
# 2. call_llm関数経由でテスト

def test_vllm_direct():
    model_name = "vllm_microsoft/Phi-4-mini-reasoning"
    model = build_model(model_name)
    response, cost = model.generate(messages, temperature=0.6)
    # ...
```

#### 4.2 test_vllm_debug.py（デバッグ版）

```python
# 短い出力でテスト（VLLM_MAX_TOKENS=100）
# リクエスト: "Count from 1 to 5. Just output the numbers."
```

#### 4.3 環境変数設定スクリプト

**setup_env.sh（本番用）**:
```bash
export VLLM_BASE_URL="http://localhost:${PORT}/v1"
export VLLM_MAX_TOKENS="16384"
export VLLM_TOP_P="0.95"
```

**setup_env_debug.sh（デバッグ用）**:
```bash
export VLLM_MAX_TOKENS="100"  # デバッグ用に短く
```

### ステップ5: 実験設定の作成

**ファイル**: `experiments/arc2/configs/config_phi4.yaml`

```yaml
task_id: 0934a4d8  # 実際のARC-AGI-2タスクID
max_num_nodes: 100
models:
  - name: "vllm_microsoft/Phi-4-mini-reasoning"
    temperature: 0.6
algo:
  class_name: "ABMCTSA"
  params:
    model_selection_strategy: "stack"
```

## ファイル構成

### 新規作成ファイル（20ファイル）

**コア実装（2ファイル）**:
- `src/ab_mcts_arc2/llm/vllm_api.py` (126行)
- 変更: `src/ab_mcts_arc2/llm/llm_builder.py`

**vLLM環境（5ファイル）**:
- `vllm_serving/pyproject.toml`
- `vllm_serving/setup_vllm.sh`
- `vllm_serving/start_vllm_phi4.sh`
- `vllm_serving/USER_README.md`
- `vllm_serving/uv.lock`

**ユーザースクリプト（4ファイル）**:
- `user_script/test_vllm.py`
- `user_script/test_vllm_debug.py`
- `user_script/setup_env.sh`
- `user_script/setup_env_debug.sh`

**ドキュメント・設定（3ファイル）**:
- `CHANGELOG.md`
- `experiments/arc2/configs/config_phi4.yaml`
- `docs/VLLM_INTEGRATION_GUIDE.md`（このファイル）

## 技術的な詳細

### コード流用率

```
vllm_api.py (126行) vs openai_api.py (254行)

流用した要素:
- リトライロジック: 100%流用
- エラーハンドリング: 100%流用
- OpenAIクライアント: 100%流用
- API呼び出しパターン: 100%流用

変更した要素:
- base_url: 環境変数から取得
- api_key: デフォルト値"EMPTY"
- PRICING: 簡略化（7行）

削減した要素:
- OPENAI_REASONING_MODELS判定
- DeepSeek/OpenRouter分岐
- to_openai_client_model_name関数
- 詳細なPRICING辞書

結果: 約50%のコード削減、約80%のロジック流用
```

### なぜOpenAI互換APIが使えるのか

vLLMは**OpenAI互換のエンドポイント**を提供：

```
OpenAI API:
POST https://api.openai.com/v1/chat/completions

vLLM API:
POST http://localhost:8000/v1/chat/completions

→ 同じリクエスト形式、同じレスポンス形式
→ 同じクライアントライブラリ（openai）が使える
```

### 依存関係の分離戦略

```
ab-mcts-arc2/                    # メインプロジェクト
├── pyproject.toml               # vLLMクライアント（openai）のみ
└── vllm_serving/                # 独立環境
    ├── pyproject.toml           # vLLMサーバー（vllm）
    └── .venv/                   # 独立した仮想環境
```

**メリット**:
- メインプロジェクトにvLLMの重い依存関係が入らない
- サーバー環境とクライアント環境を別々に管理
- それぞれ独立してアップデート可能

## トラブルシューティング

### 問題1: start_vllm_phi4.shが動かない

**症状**:
```bash
OSError: [Errno 98] Address already in use
```

**原因**:
- 古い方法（`python -m vllm.entrypoints.openai.api_server`）は内部的にRayを使用
- 複雑な初期化プロセスでポート競合が発生しやすい

**解決策**: 新しいvLLM CLIコマンドを直接使用

```bash
cd vllm_serving

# 推奨: 新しいコマンド
uv run vllm serve microsoft/Phi-4-mini-reasoning \
    --port 8001 \
    --trust-remote-code \
    --max-model-len 32768

# 非推奨: 古いコマンド（動かない可能性あり）
# uv run python -m vllm.entrypoints.openai.api_server ...
```

### 問題2: max_tokensエラー

**症状**:
```
'max_tokens' is too large: 32767. This model's maximum context length is 32768 tokens
```

**原因**: 入力トークン数 + max_tokens > max-model-len (32768)

**解決策**: max_tokensを減らす

```bash
# デフォルトは16384（推奨）
export VLLM_MAX_TOKENS="16384"

# より長い出力が必要な場合
export VLLM_MAX_TOKENS="20000"
```

### 問題3: ポート8000が既に使用中

**症状**:
```bash
lsof -i:8000
# 他のユーザーのプロセスが表示される
```

**解決策**: 別のポートを使用

```bash
# ポート8001で起動
VLLM_PORT=8001 bash vllm_serving/start_vllm_phi4.sh

# または直接コマンド実行
cd vllm_serving
uv run vllm serve microsoft/Phi-4-mini-reasoning --port 8001 ...
```

クライアント側も変更:
```bash
source user_script/setup_env.sh 8001
```

### 問題4: task_id not found

**症状**:
```
Task 0 not found
```

**原因**: `task_id: 0`は存在しないファイル名

**解決策**: 実際のタスクIDを使用

```bash
# タスクIDを確認
ls ARC-AGI-2/data/evaluation/ | head -5

# コマンドラインで指定
cd experiments/arc2
TASK_ID=0934a4d8 uv run python run.py \
    --config-name=config_phi4 \
    task_id=0934a4d8
```

## ベストプラクティス

### 1. vLLMサーバーの起動

```bash
# 推奨: vllm serve コマンドを直接使用
cd vllm_serving
uv run vllm serve microsoft/Phi-4-mini-reasoning \
    --port 8001 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 32768 \
    --trust-remote-code
```

### 2. 環境変数の設定

```bash
# setup_env.shを使用（推奨）
source user_script/setup_env.sh 8001

# または手動設定
export VLLM_BASE_URL="http://localhost:8001/v1"
export VLLM_API_KEY="EMPTY"
export VLLM_MAX_TOKENS="16384"
export VLLM_TOP_P="0.95"
```

### 3. テストの実行

```bash
# まずデバッグ版でテスト
source user_script/setup_env_debug.sh 8001
uv run python user_script/test_vllm_debug.py

# 成功したら通常版
source user_script/setup_env.sh 8001
uv run python user_script/test_vllm.py
```

### 4. 実験の実行

```bash
cd experiments/arc2

# 環境変数とコマンドラインで指定
TASK_ID=0934a4d8 uv run python run.py \
    --config-name=config_phi4 \
    task_id=0934a4d8 \
    max_num_nodes=100
```

## まとめ

vLLM統合は以下の原則に従って実装されました：

1. **既存実装の最大限活用** - openai_api.pyから80%のコードを流用
2. **依存関係の明確な分離** - サーバーとクライアントを独立管理
3. **OpenAI互換APIの活用** - 同じクライアントライブラリで実装コストを削減
4. **環境変数による柔軟性** - 実行環境に応じた設定変更が容易

この設計により、高い信頼性と低い実装コストを両立できました。
