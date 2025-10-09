# デバッグスクリプトの使い方

アルゴリズムの動作を理解するためのデバッグスクリプトを2つ用意しました。

## 1. `simple_debug.py` - 最もシンプル（推奨）

**特徴:**
- 1ステップ（ルートノードの生成）のみを実行
- プロンプトと生成結果を**完全に**表示
- アルゴリズムの基本動作を理解するのに最適

**実行方法:**
```bash
cd /Users/koko/work/ab-mcts-arc2

# uvで実行（推奨）
uv run user_script/simple_debug.py

# または直接実行
./user_script/simple_debug.py
```

**出力内容:**
- タスク情報（demos、testsの数）
- 生成された初期プロンプト全文
- LLMの生成結果全文
- 評価結果とスコア
- 実行時間とコスト

**出力ファイル:**
- `debug_output/simple_debug_{task_id}_{timestamp}.json` に結果が保存されます

**カスタマイズ:**
スクリプトの上部で以下を変更できます：
```python
task_id = "007bbfb7"  # 使用するタスクID
model_name = "o4-mini-2025-04-16"  # 使用するモデル
temperature = 0.6  # 温度パラメータ
```

---

## 2. `debug_algorithm.py` - より詳細な観察

**特徴:**
- 5ステップの探索を実行
- 各ステップで詳細なログを出力
- 探索木の成長過程を観察できる

**実行方法:**
```bash
cd /Users/koko/work/ab-mcts-arc2

# uvで実行（推奨）
uv run user_script/debug_algorithm.py

# または直接実行
./user_script/debug_algorithm.py
```

**出力内容:**
- 各ステップの詳細（プロンプト、生成結果、評価）
- 探索木のノード数の変化
- ベストスコアの推移
- 最終結果のサマリー

**出力ファイル:**
- `debug_output/debug_result_{task_id}.json` に最終結果が保存されます

**カスタマイズ:**
スクリプト内で以下を変更できます：
```python
task_id = "007bbfb7"  # タスクID
max_steps = 5  # ステップ数（現在は5）
model_config = {
    "name": "o4-mini-2025-04-16",
    "temperature": 0.6
}
```

---

## どちらを使うべきか？

### `simple_debug.py` を使う場合：
- ✅ アルゴリズムの基本動作を理解したい
- ✅ プロンプトの内容を確認したい
- ✅ 1回の生成でどのような結果が返ってくるか見たい
- ✅ 素早く動作確認したい（実行時間が短い）

### `debug_algorithm.py` を使う場合：
- ✅ 探索木がどのように成長するか見たい
- ✅ 複数ステップでのスコア改善を観察したい
- ✅ AB-MCTSアルゴリズムの動作を理解したい

---

## トラブルシューティング

### エラー: "Task file not found"
タスクファイルのパスを確認してください：
```bash
ls ARC-AGI-2/data/evaluation/*.json
```

存在するタスクIDをスクリプトに指定してください。

### エラー: "Model not found" または API エラー
1. `.env` ファイルにAPIキーが設定されているか確認
2. 使用するモデル名が正しいか確認
3. vLLMサーバーが起動しているか確認（vLLMモデルを使う場合）

### 実行が遅い
- vLLMの場合：サーバーの起動状態を確認
- APIの場合：ネットワーク接続を確認
- `max_steps` を減らす（`debug_algorithm.py`の場合）

---

## 理解を深めるための次のステップ

1. **simple_debug.pyを実行**
   - プロンプトの構造を理解
   - 生成結果の形式を確認
   - 評価がどのように行われるか理解

2. **異なるタスクIDで試す**
   - 簡単なタスク、難しいタスクで比較
   - プロンプトの違いを観察

3. **debug_algorithm.pyを実行**
   - 探索木の成長を観察
   - スコアがどのように改善されるか確認

4. **パラメータを変更して実験**
   - `temperature` を変えて生成結果の多様性を観察
   - `max_steps` を変えて探索の深さを調整

5. **コードを読む**
   - `experiments/arc2/run.py` - メインの実行ロジック
   - `src/ab_mcts_arc2/llm/llm_builder.py` - LLM呼び出し
   - `src/ab_mcts_arc2/tasks/arc/task.py` - タスク評価
   - `experiments/arc2/prompt.py` - プロンプト生成

---

## 生成長を調整する方法（オプション）

生成長（max_tokens）を調整したい場合は、以下のファイルを編集します：

### vLLMの場合:
`src/ab_mcts_arc2/llm/vllm_api.py` の `generate` メソッド内：
```python
response = self.client.completions.create(
    model=self.model_name,
    prompt=prompt_str,
    temperature=temperature,
    max_tokens=512,  # ここを変更（デフォルトは2048など）
    # ...
)
```

### OpenAI APIの場合:
`src/ab_mcts_arc2/llm/openai_api.py` の `generate` メソッド内：
```python
response = openai.ChatCompletion.create(
    model=self.model_name,
    messages=messages,
    temperature=temperature,
    max_tokens=512,  # ここを変更
    # ...
)
```

**注意:** コードを直接編集せずに設定ファイルで制御したい場合は、設定システムの拡張が必要です。

---

## 出力例

### simple_debug.py の出力例：
```
🔍 Simple Debug - Single Step Execution
================================================================================
Task ID: 007bbfb7
Model: o4-mini-2025-04-16
Temperature: 0.6
================================================================================

📂 Loading task...
✅ Task loaded:
   - Training examples (demos): 3
   - Test examples: 1

📊 Demo example shapes:
   Demo 0: input=(3, 3), output=(3, 3)
   Demo 1: input=(3, 3), output=(3, 3)
   Demo 2: input=(3, 3), output=(3, 3)

📝 Creating prompt template...
✅ Prompt template created

📨 Generating initial prompt...
✅ Initial prompt generated (2345 characters)

================================================================================
📄 FULL INITIAL PROMPT:
================================================================================
[プロンプトの内容が表示される]
================================================================================

🤖 Calling LLM: o4-mini-2025-04-16...
✅ LLM response received!
   - Time: 3.45s
   - Cost: $0.000123
   - Length: 1234 characters

================================================================================
📤 FULL LLM GENERATION:
================================================================================
[生成結果が表示される]
================================================================================

🧪 Evaluating generated code...
✅ Evaluation completed in 0.23s

📊 Evaluation Results:
   - Overall Score: 0.667
   - Number of examples: 3
   ✅ Example 0: score=1.000
   ✅ Example 1: score=1.000
   ❌ Example 2: score=0.000

✅ Results saved to: debug_output/simple_debug_007bbfb7_20251007_123456.json

================================================================================
📊 SUMMARY
================================================================================
Task: 007bbfb7
Model: o4-mini-2025-04-16
Score: 0.667
Cost: $0.000123
LLM Time: 3.45s
Eval Time: 0.23s
Total Time: 3.68s
================================================================================

✨ Simple debug completed!
```

---

## 質問やフィードバック

スクリプトの動作について質問がある場合や、さらなる機能が必要な場合は、お気軽にお知らせください！
