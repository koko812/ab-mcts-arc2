# vLLM Serving Environment

このディレクトリはvLLMサーバー専用の独立した環境です。
メインプロジェクト（ab-mcts-arc2）とは依存関係を分離しています。

## セットアップ

### 1. 初回セットアップ

```bash
# vllm_servingディレクトリで実行
bash vllm_serving/setup_vllm.sh
```

このスクリプトは以下を実行します：
- 独立したuvプロジェクトの初期化（`--no-workspace`）
- vLLMのインストール

### 2. 手動セットアップ（オプション）

setup_vllm.shを使わない場合：

```bash
cd vllm_serving

# 依存関係を同期（pyproject.tomlは既にリポジトリに含まれています）
uv sync
```

## vLLMサーバーの起動

```bash
# GPU 1枚で起動（デフォルト）
bash vllm_serving/start_vllm_phi4.sh

# GPU 2枚で起動（Tensor Parallelism）
bash vllm_serving/start_vllm_phi4.sh 2

# GPU 1枚、メモリ使用率80%で起動
bash vllm_serving/start_vllm_phi4.sh 1 0.8
```

## サーバーが起動したら

別のターミナルで環境変数を設定：

```bash
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_API_KEY="EMPTY"
```

その後、メインプロジェクトからテストまたは実験を実行：

```bash
# テスト
uv run python user_script/test_vllm.py

# 実験
cd experiments/arc2
uv run python run.py --config-name=config_phi4 task_id=0
```

## ファイル構成

```
vllm_serving/
├── USER_README.md         # このファイル
├── setup_vllm.sh          # セットアップスクリプト
├── start_vllm_phi4.sh     # サーバー起動スクリプト
├── pyproject.toml         # vLLM専用の依存関係（setup後に生成）
└── uv.lock                # ロックファイル（setup後に生成）
```

## なぜ分離するのか？

- **依存関係の分離**: vLLMは大きな依存関係を持つため、メインプロジェクトと分離
- **環境の独立**: サーバー環境とクライアント環境を別々に管理
- **メンテナンス性**: それぞれの環境を独立してアップデート可能

## トラブルシューティング

### GPU メモリ不足

```bash
# GPU使用率を下げる
bash vllm_serving/start_vllm_phi4.sh 1 0.8

# 複数GPUでTensor Parallelismを使う
bash vllm_serving/start_vllm_phi4.sh 2
```

### モデルのダウンロード

初回起動時はHugging Faceからモデルをダウンロードします。
キャッシュ: `~/.cache/huggingface/`

### サーバーの確認

```bash
# サーバーが起動しているか確認
curl http://localhost:8000/v1/models
```
