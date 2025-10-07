# Phi-4 クイックスタートガイド

このガイドでは、vLLM + Phi-4-mini-reasoningを使ってARC-AGI-2問題を解く最も簡単な方法を説明します。

## 🚀 3ステップで実行

### ステップ1: 初回セットアップ（最初の1回だけ）

```bash
# 1. メインプロジェクトの依存関係をインストール
uv sync

# 2. vLLM環境をセットアップ
bash vllm_serving/setup_vllm.sh
```

### ステップ2: vLLMサーバーを起動（ターミナル1）

```bash
cd vllm_serving

uv run vllm serve microsoft/Phi-4-mini-reasoning \
    --port 8001 \
    --trust-remote-code \
    --max-model-len 32768
```

**起動確認**: "Uvicorn running on http://0.0.0.0:8001" と表示されればOK

### ステップ3: 実験を実行（ターミナル2）

```bash
# シンプルな方法
bash user_script/run_phi4_experiment.sh 0934a4d8 100

# または手動で実行
source user_script/setup_env.sh 8001
cd experiments/arc2
TASK_ID=0934a4d8 uv run python run.py \
    --config-name=config_phi4 \
    task_id=0934a4d8 \
    max_num_nodes=100
```

**完了！** 結果は `experiments/arc2/outputs/` に保存されます。

---

## 📋 詳細な実行方法

### 実験パラメータのカスタマイズ

```bash
# タスクIDを変更
bash user_script/run_phi4_experiment.sh 135a2760 100

# ノード数を変更
bash user_script/run_phi4_experiment.sh 0934a4d8 50

# 複数タスクを順次実行
for task in 0934a4d8 135a2760 136b0064; do
    bash user_script/run_phi4_experiment.sh $task 100
done
```

### vLLMサーバーのオプション

```bash
# GPU 2枚で並列実行
uv run vllm serve microsoft/Phi-4-mini-reasoning \
    --port 8001 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code \
    --max-model-len 32768

# デバッグ用（短い出力）
export VLLM_MAX_TOKENS="100"
```

---

## 📂 結果の確認

### 出力ディレクトリ構造

```
experiments/arc2/outputs/arc/phi4_TASK_ID_TIMESTAMP/
├── llm_logs/                    # 各LLM呼び出しの詳細ログ
│   └── log_*.txt
├── costs/                       # コストと実行時間
│   ├── cost_summary.json
│   └── time_summary.json
├── checkpoints/                 # 探索木のチェックポイント
│   └── checkpoint_latest.pkl
└── .hydra/                      # 実行時の設定
    └── config.yaml
```

### コストと時間の確認

```bash
# 最新の実験結果を確認
cd experiments/arc2/outputs/arc
ls -lt | head -5

# コストサマリーを表示
cat phi4_*/costs/cost_summary.json

# 実行時間サマリーを表示
cat phi4_*/costs/time_summary.json
```

---

## 🔧 トラブルシューティング

### よくある問題と解決策

#### 1. vLLMサーバーが起動しない

**症状**: `Address already in use` エラー

**解決策**: 別のポートを使用
```bash
# ポート8002で起動
uv run vllm serve microsoft/Phi-4-mini-reasoning --port 8002 ...

# 環境変数も変更
source user_script/setup_env.sh 8002
```

#### 2. ログファイルエラー

**症状**: `FileNotFoundError`

**解決策**: 最新のコードをpull（既に修正済み）
```bash
git pull origin claude
```

#### 3. max_tokens エラー

**症状**: `max_tokens is too large`

**解決策**: 環境変数を調整
```bash
export VLLM_MAX_TOKENS="16384"  # デフォルト値
```

#### 4. Task not found

**症状**: `Task 0 not found`

**解決策**: 実際のタスクIDを使用
```bash
# タスクIDを確認
ls ARC-AGI-2/data/evaluation/ | head -10

# 正しいIDで実行
bash user_script/run_phi4_experiment.sh 0934a4d8 100
```

---

## 📚 さらに詳しく知りたい場合

### ドキュメント

- **詳細な実装ガイド**: [docs/VLLM_INTEGRATION_GUIDE.md](docs/VLLM_INTEGRATION_GUIDE.md)
  - 実装手順の詳細
  - コード流用率の分析
  - 技術的な設計決定

- **vLLM環境の詳細**: [vllm_serving/USER_README.md](vllm_serving/USER_README.md)
  - セットアップ手順
  - トラブルシューティング

- **ユーザースクリプト**: [user_script/USER_README.md](user_script/USER_README.md)
  - テストスクリプトの使い方
  - 環境変数の設定

- **変更履歴**: [CHANGELOG.md](CHANGELOG.md)
  - 追加された機能
  - 変更されたファイル

### 使用可能なコマンド一覧

```bash
# セットアップ
bash vllm_serving/setup_vllm.sh              # vLLM環境セットアップ

# サーバー起動（いずれか一つ）
bash vllm_serving/start_vllm_phi4.sh 1       # スクリプト（動かない場合あり）
cd vllm_serving && uv run vllm serve ...     # 直接実行（推奨）

# 環境変数設定
source user_script/setup_env.sh 8001         # 本番用
source user_script/setup_env_debug.sh 8001   # デバッグ用

# テスト
uv run python user_script/test_vllm.py       # 通常テスト
uv run python user_script/test_vllm_debug.py # デバッグテスト

# 実験実行
bash user_script/run_phi4_experiment.sh <TASK_ID> <MAX_NODES>
```

---

## 🎯 典型的な作業フロー

### 新しいタスクで実験する場合

```bash
# 1. vLLMサーバーが起動していることを確認
curl http://localhost:8001/v1/models

# 2. タスクIDを決定
TASK=135a2760

# 3. 実験実行
bash user_script/run_phi4_experiment.sh $TASK 100

# 4. 結果を確認
cd experiments/arc2/outputs/arc
ls -lt | head -1
cat phi4_${TASK}_*/costs/cost_summary.json
```

### デバッグモードで動作確認

```bash
# 1. デバッグ用環境変数を設定（短い出力）
source user_script/setup_env_debug.sh 8001

# 2. 少ないノード数でテスト実行
bash user_script/run_phi4_experiment.sh 0934a4d8 10

# 3. ログを確認
tail -f experiments/arc2/outputs/arc/phi4_*/llm_logs/log_*.txt
```

### 複数タスクを並列実行（注意: リソース消費大）

```bash
# 異なるポートでvLLMサーバーを起動
# ターミナル1
cd vllm_serving
uv run vllm serve microsoft/Phi-4-mini-reasoning --port 8001 ...

# ターミナル2
cd vllm_serving
uv run vllm serve microsoft/Phi-4-mini-reasoning --port 8002 ...

# 異なるターミナルで実験を実行
# ターミナル3
source user_script/setup_env.sh 8001
bash user_script/run_phi4_experiment.sh 0934a4d8 100

# ターミナル4
source user_script/setup_env.sh 8002
bash user_script/run_phi4_experiment.sh 135a2760 100
```

---

## 💡 Tips

### より速く実行するには

- **max_num_nodes を減らす**: `10-50`で試してから本番実行
- **GPU並列を使う**: `--tensor-parallel-size 2`
- **デバッグモードで確認**: `VLLM_MAX_TOKENS=100`で高速化

### コストを抑えるには

- vLLMはローカル実行なので**基本的に無料**（電気代のみ）
- `cost_summary.json`の値は$0になるはず

### 実験を中断・再開するには

```bash
# チェックポイントから再開
cd experiments/arc2
uv run python run.py \
    --config-name=config_phi4 \
    task_id=0934a4d8 \
    checkpoint_path=outputs/arc/phi4_*/checkpoints/checkpoint_latest.pkl
```

---

## 📞 サポート

問題が発生した場合:

1. **まずは確認**: [docs/VLLM_INTEGRATION_GUIDE.md](docs/VLLM_INTEGRATION_GUIDE.md)のトラブルシューティング
2. **ログを確認**: `experiments/arc2/outputs/arc/phi4_*/llm_logs/`
3. **GitHubのIssue**: 問題を報告

---

## ✅ チェックリスト

作業を引き継ぐ際のチェックリスト:

- [ ] `uv sync` を実行済み
- [ ] `bash vllm_serving/setup_vllm.sh` を実行済み
- [ ] vLLMサーバーが起動できる
- [ ] `curl http://localhost:8001/v1/models` が成功する
- [ ] テストが通る: `uv run python user_script/test_vllm.py`
- [ ] 実験が実行できる: `bash user_script/run_phi4_experiment.sh 0934a4d8 10`
- [ ] 結果が保存されている: `ls experiments/arc2/outputs/arc/`

全てにチェックが入れば、環境は正しくセットアップされています！
