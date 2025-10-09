# 編集ログ: `outputs/plots` をリポジトリに残す設定

- **実施日**: 2025-10-09
- **背景**: 実験結果が `outputs/` 以下に大量に生成されるため Git から外したい一方、プロットだけは履歴管理したい。
- **対応内容**: `.gitignore` を編集し、`outputs/` 以下は原則無視しつつ `outputs/plots/` だけは追跡対象に戻した。
- **実行したコマンド**:
  ```bash
  apply_patch <<'EOF'
  *** Update File: .gitignore
  @@
  -.env
  -outputs/
  +.env
  +outputs/*
  +!outputs/plots/
  +!outputs/plots/**
  logging/
  evals/
  EOF
  ```
- **効果**: 実験ごとの生成物（`outputs/*`）はコミット対象外になり、可視化結果の PNG だけが `outputs/plots/` に残る。今後プロットを共有したいときはこの設定のまま追加できる。
