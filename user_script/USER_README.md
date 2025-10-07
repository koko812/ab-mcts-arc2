# User Scripts for vLLM Integration

このディレクトリには、vLLM統合のためのユーザースクリプトが含まれています。

## ファイル一覧

### 1. `test_vllm.py`
vLLM統合が正しく動作するかテストするスクリプト（通常版）

### 2. `test_vllm_debug.py`
デバッグ用の短い出力でテストするスクリプト（max_tokens=100）

**使い方:**
```bash
# 1. vLLMサーバーを起動（別ターミナル）
bash vllm_serving/start_vllm_phi4.sh

# 2. 環境変数を設定
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_API_KEY="EMPTY"

# 3. テスト実行
uv run python user_script/test_vllm.py
```

**テスト内容:**
- Test 1: VLLMAPIModelクラスの直接テスト
- Test 2: call_llm関数経由でのテスト

## セットアップ手順

### Step 0: vLLM環境のセットアップ（初回のみ）

```bash
# vLLM専用環境をセットアップ
bash vllm_serving/setup_vllm.sh
```

詳細は [vllm_serving/USER_README.md](../vllm_serving/USER_README.md) を参照

### Step 1: vLLMサーバーの起動

別のターミナルで以下を実行:

```bash
bash vllm_serving/start_vllm_phi4.sh
```

サーバーが起動すると、以下のようなメッセージが表示されます:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: 環境変数の設定

実験を実行するターミナルで:

**通常版（本番用）:**
```bash
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_API_KEY="EMPTY"
export VLLM_MAX_TOKENS="32767"  # デフォルト値
export VLLM_TOP_P="0.95"        # デフォルト値
```

**デバッグ版（短い出力）:**
```bash
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_API_KEY="EMPTY"
export VLLM_MAX_TOKENS="100"    # デバッグ用に短く
export VLLM_TOP_P="0.95"
```

### Step 3: テストの実行

**通常版テスト:**
```bash
uv run python user_script/test_vllm.py
```

**デバッグ版テスト（短い出力で確認）:**
```bash
# 環境変数でVLLM_MAX_TOKENS=100を設定してから実行
uv run python user_script/test_vllm_debug.py
```

全てのテストが成功すれば、vLLM統合が正しく動作しています。

### Step 4: 実験の実行

```bash
cd experiments/arc2
uv run python run.py --config-name=config_phi4 task_id=0
```

## トラブルシューティング

### vLLMサーバーに接続できない

**確認事項:**
1. vLLMサーバーが起動しているか
   ```bash
   curl http://localhost:8000/v1/models
   ```

2. 環境変数が設定されているか
   ```bash
   echo $VLLM_BASE_URL
   echo $VLLM_API_KEY
   ```

### GPU メモリ不足

**対処法:**
- GPU使用率を下げる: `bash user_script/start_vllm_phi4.sh 2 0.8`
- Tensor Parallel Sizeを増やす: `bash user_script/start_vllm_phi4.sh 4`

### モデルのダウンロードが遅い

初回起動時はHugging Faceからモデルをダウンロードするため時間がかかります。
キャッシュは `~/.cache/huggingface/` に保存されます。

## 関連ファイル

- [experiments/arc2/configs/config_phi4.yaml](../experiments/arc2/configs/config_phi4.yaml) - Phi-4用の設定
- [src/ab_mcts_arc2/llm/vllm_api.py](../src/ab_mcts_arc2/llm/vllm_api.py) - vLLM APIクライアント
- [src/ab_mcts_arc2/llm/llm_builder.py](../src/ab_mcts_arc2/llm/llm_builder.py) - モデルビルダー
