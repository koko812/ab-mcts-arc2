# run.py 実行フローとトレース指針

目的: `experiments/arc2/run.py` を実行した際の処理順序を整理し、どこで LLM の `generate` が呼ばれているか、どの部分でノードの評価が行われるかを明確にする。

## 高レベルの流れ

- Hydra によって `main(cfg)` が起動する（`experiments/arc2/run.py`）。
- 問題データ読み込み、`BaselinePrompt` の生成、`generate_fns`（モデル名ごとの partial 関数）を準備。
- 探索アルゴリズム（treequest）がループで `algo.step(..., generate_fns)` を呼び、ノードを展開・評価する。
- 各ノードの処理は `generate_fn`（`experiments/arc2/run.py` 内）で行われる。

## `generate_fn` の責務（該当ファイル: `experiments/arc2/run.py`）

- state が `None` のときは `prompt_template.initial_prompt()` を使う。
- state があるときは `prompt_template.feedback_prompt(..., generation_result=state.generation_result)` を呼び、前回の生成を組み込んだプロンプトを作る。
- 作成したプロンプトを `messages = [{"role": "user", "content": feedback_prompt}]` の形にして `call_llm(model_name, model_temp, messages)` を呼ぶ。
- `call_llm` の返り値（生成文字列とコスト）を用いて `GenerationResult` を作り、`task.generate_eval_results(...)` を呼んで評価を行い、ノードのスコアを計算する。

## `model.generate` が呼ばれる箇所

- `call_llm(model_name, model_temp, messages)`（`src/ab_mcts_arc2/llm/llm_builder.py`）
  - 内部で `build_model(model_name)` を呼び、該当の Model インスタンス（`VLLMAPIModel`, `OpenAIAPIModel`, `ClaudeBedrockAPIModel` など）を生成する。
  - その後 `model.generate(messages, model_temp)` を呼び、各 LLM 実装が API/サーバへ `messages` を渡して応答を取得する。

該当モデル実装ファイル例:

- `src/ab_mcts_arc2/llm/vllm_api.py` → `VLLMAPIModel.generate`
- `src/ab_mcts_arc2/llm/openai_api.py` → `OpenAIAPIModel.generate`
- `src/ab_mcts_arc2/llm/claude_api.py` → `ClaudeBedrockAPIModel.generate`

## ノード評価の実装場所

- ノードからの評価呼び出し: `task.generate_eval_results(llm_answer=result, kind='transform')`（`experiments/arc2/run.py` の `generate_fn`）
- タスク実装（ARC の例）: `src/ab_mcts_arc2/tasks/arc/task.py` の `generate_eval_results`。
  - ここで `GenerationResult.parse_python_code()` によって生成から Python コードを取り出す。
  - 各デモやテストについて `eval_if_test_pass(...)` を呼び出す。
- コード実行・評価の本体: `src/ab_mcts_arc2/evaluate_code.py`。
  - `generate_code_and_test`, `eval_if_test_pass`, `untrusted_check`, `unsafe_execute` により、分離プロセスで生成コードに対するユニットテストを実行し、成功/失敗/タイムアウトを判定する。
- 評価結果の型: `src/ab_mcts_arc2/eval_result.py`（`EvalResult`, `EvalResultWithAns` など）。

## 追跡（トレース）をつけるための提案

1. ログ出力の確認:
   - 実行時、Hydra の出力ディレクトリに `llm_logs/log_<timestamp>_<model>.txt` が作られる。ここに `generation` と `cost` が JSON で保存されるため、まずこのファイルを確認する。

2. 簡易デバッグ挿入（推奨場所）:
   - `src/ab_mcts_arc2/llm/llm_builder.py::call_llm` の直前／直後にログを追加して、どのモデルへ `messages` を渡したかを出力する。
   - `experiments/arc2/run.py::generate_fn` に `eval_results` の中身（各例の出力）を `llm_logs` に追加で保存する。

3. 例: `call_llm` に追加する簡単なログ（擬似）:

```
# call_llm の先頭で
print(f"Calling model.generate for {model_name}; prompt length: {len(messages[0]['content'])}")
```

（実際に自動でパッチを当てることも可能です。希望があれば行います。）

## 次のステップ候補

- すでに計画されているように、`generate_fn` にトレースを追加して実行し、`llm_logs` と合わせて確認する。
- 評価ポリシーを変更する場合は `src/ab_mcts_arc2/eval_result.py` または `src/ab_mcts_arc2/evaluate_code.py` を編集する。

---

保存日: 2025-10-07

## 詳細な実行フロー（ステップバイステップ）

以下は `experiments/arc2/run.py` を Hydra 経由で実行したときに起きる処理の詳細な順序です。デバッグやトレースを入れるときはこの順序に沿ってログを追加していくと追いやすいです。

1. Hydra エントリポイント
  - `@hydra.main` により `main(cfg)` が呼ばれる。`cfg` は `configs/*` から読み込まれる。

2. タスクとプロンプトの初期化
  - ARC 問題 JSON を `ARCProblem.load_file(...)` で読み込む。
  - `prompt_template = BaselinePrompt(prompt_config=..., problem=task)` を構築。

3. generate_fns の作成
  - `cfg['models']` の設定を元に、各モデル用の `generate_fn` を partial で束縛して `generate_fns` 辞書を作る。
  - これにより探索アルゴリズムはモデル名をキーに `generate_fn` を呼べるようになる。

4. 探索アルゴリズムのループ
  - `algo = algo_cls(...)`（treequest のアルゴリズムクラス）。
  - `search_tree = algo.init_tree()` で初期化。
  - ループで `search_tree = algo.step(search_tree, generate_fns)` を呼ぶ。`algo.step` の内部で必要に応じて `generate_fns[model_name]()` が呼ばれ、ノードの生成と評価が行われる。

5. ノード単位の処理: `generate_fn(...)` の実行（`experiments/arc2/run.py`）
  - 引数: state（前ノードの NodeState か None）、task、prompt_template、model_name、model_temp 等。
  - state が None の場合: `messages = [{'role': 'user', 'content': prompt_template.initial_prompt()}]` を作成。
  - state がある場合: `feedback_prompt = prompt_template.feedback_prompt(..., generation_result=state.generation_result)` を作成し、`messages = [{'role': 'user', 'content': feedback_prompt}]` を作る。
  - 次に `generation, cost = call_llm(model_name, model_temp, messages)` を呼ぶ。ここが実際に LLM に問い合わせる箇所。
  - 返ってきた `generation` と `cost` から `GenerationResult(request=GenerationRequest(messages=messages), generation=generation)` を作成する。
  - `eval_results = task.generate_eval_results(llm_answer=result, kind='transform')` を呼び評価を取得し、スコアを計算して `NodeState` を返す。

6. LLM 呼び出しのチェーン
  - `call_llm(model_name, model_temp, messages)`（`src/ab_mcts_arc2/llm/llm_builder.py`）
    - `model = build_model(model_name)` で実装クラスを作る（`VLLMAPIModel`, `OpenAIAPIModel`, `ClaudeBedrockAPIModel` など）。
    - `return model.generate(messages, model_temp)` を呼ぶ。
  - 各モデルの `generate` 実装が API クライアントに `messages` を渡し、応答を返す。

7. 評価の詳細
  - `task.generate_eval_results`（例: `src/ab_mcts_arc2/tasks/arc/task.py`）は `GenerationResult.parse_python_code()` で生成から Python コードを取り出し、`run_transform_on_demos/test` を通して `eval_if_test_pass` を呼ぶ。
  - `eval_if_test_pass`（`src/ab_mcts_arc2/evaluate_code.py`）はテンプレートからユニットテストコードを生成し、`untrusted_check` → `unsafe_execute` で隔離プロセス中に `exec` + `unittest` を実行して判定する。

## 主要なファイルと関数（参照用）

- 実行の出発点: `experiments/arc2/run.py` (`main`, `generate_fn`)
- LLM 呼び出し: `src/ab_mcts_arc2/llm/llm_builder.py` (`call_llm`, `build_model`)
- vLLM 実装: `src/ab_mcts_arc2/llm/vllm_api.py` (`VLLMAPIModel.generate`)
- OpenAI 実装: `src/ab_mcts_arc2/llm/openai_api.py` (`OpenAIAPIModel.generate`)
- Claude 実装: `src/ab_mcts_arc2/llm/claude_api.py` (`ClaudeBedrockAPIModel.generate`)
- タスク評価: `src/ab_mcts_arc2/tasks/arc/task.py` (`generate_eval_results` 等)
- コード評価実行: `src/ab_mcts_arc2/evaluate_code.py`（`eval_if_test_pass`, `untrusted_check`, `unsafe_execute`）
- 評価結果クラス: `src/ab_mcts_arc2/eval_result.py`

## 実行時ログと出力場所

- `generate_fn` は LLM 応答を Hydra の出力ディレクトリ内 `llm_logs` に JSON ファイルとして保存しています（`log_<timestamp>_<model>.txt`）。このファイルには model, cost, result（GenerationResult の dataclass）が含まれます。
- 実行中の vLLM サーバーの stdout/stderr ログ（提示されているログ行）はモデルサーバ側のメトリクスで、トークン生成レートや KV キャッシュ利用率、リクエスト数などが出力されます。

例: run.py 側にあるログ保存の最小例（参考）

```python
# 実際のコードは run.py にありますが、ここでは保存の意図を示す縮約例です
log_txt.write_text(json.dumps({
   'model': model_name,
   'cost': cost,
   'result': dataclasses.asdict(result)
}, indent=4))
```

## vLLM のスループットが低いときの診断と改善案

あなたが貼ってくれた vLLM のログ（例）:

(APIServer pid=4169824) INFO 10-07 16:37:49 [loggers.py:127] Engine 000: Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 36.4 tokens/s, Running: 1 reqs, Waiting: 0 reqs, GPU KV cache usage: 10.9%, Prefix cache hit rate: 88.2%

これは「1 リクエスト・生成トークンレート ~36 tokens/s」であり、もし GPU がある程度空いているなら低いと感じるのは妥当です。原因は複数考えられます。下に診断ステップと改善案を示します。

### 診断ステップ（優先度順）

1. 同時リクエスト数（Concurrency）を確認
  - ログの `Running: 1 reqs` は並列リクエストが 1 であることを示します。スループットを出すには同時に複数リクエストを流すのが有効です。

2. バッチングの有無とプロンプト長
  - `Avg prompt throughput: 0.0 tokens/s` が 0 なのはプロンプトトークンの計測が無効化されているか、プロンプトが非常に短いか、サーバの計測差異です。
  - 1 リクエストあたりの max_tokens 設定や prompt 長が小さいと、GPU の並列化が活かせず低スループットになります。

3. GPU 使用率と NVidia ツールでの確認（もし GPU を使っているなら）
  - ローカル GPU の場合:

```bash
nvidia-smi -l 1
```

  - GPU メモリ使用量と GPU% を観察。GPU% が低ければモデル推論がボトルネックになっていない（I/Oやスレッド・シングルスレッド待ち等が原因）。

4. vLLM サーバの設定確認
  - vLLM を何で起動しているか（単一スレッド/マルチワーカー、num_beam, num_threads, kv_cache 等）を確認。
  - 環境変数（例: `VLLM_*`）やサーバ起動引数で `--num-gpus`, `--num-threads`, `--tokenizer` などが適切か確認。

5. リクエストパターンの確認
  - クライアント側から短時間にリクエストが順次送られていないか（パイプライン化されていない）が重要。`generate_fn` が逐次的に呼ばれている場合、並列処理レベルを上げる必要がある。

### 改善案（現実的で効果の高い順）

1. 並列リクエストを増やす（アプリ側）
  - treequest の設定や generate の呼び出しを並列化して複数リクエストを同時に送る。例えば `algo.step` を並列化する、もしくは generate_fns を並列ワーカーで呼ぶ。
  - 注意: 並列リクエストを増やすとメモリ（KV キャッシュ）を多く消費するため GPU メモリの余裕を確認する。

2. サーバ側のスレッド数 / ワーカー数調整
  - vLLM の起動引数によりスレッド数やバッチングのしやすさを変えられる場合があります。ドキュメントに沿って `num_threads` / `num_gpus`／`max_batch_size` 等を調整してみてください。

3. バッチングを活用する
  - 複数リクエストを vLLM 側でバッチとして処理できるようにする。クライアント側で少し待って複数リクエストをまとめるなど。

4. プロンプト最適化
  - prompt が非常に短い／長すぎる場合にスループットが下がることがあるため、プロンプト形式（テンプレート）を見直し、必要最小限にする。

5. トークン関連パラメータの調整
  - `max_tokens`、`top_p`、`temperature` が生成のコスト・スループットに影響する場合がある。`max_tokens` を小さくして応答を短くする試験をしてみる。

6. ハードウェア/ドライバの確認
  - GPU のドライバが最新か、CUDA/cuDNN のバージョンや PyTorch 等（vLLM が依存しているコンポーネント）が適切か確認。

### 具体的な短期アクション（Try-list）

1. vLLM サーバへの簡易プロービング

```bash
# モデルリストの確認（vLLM の OpenAI 互換エンドポイントが稼働していれば）
curl -s http://localhost:8000/v1/models | jq .

# サーバ側のヘルスや stats があれば叩く。vLLM の実装による。
curl -s http://localhost:8000/health
```

2. クライアント側で同時に複数リクエストを投げる簡易テスト（Python、並列化）

```python
import concurrent.futures
from ab_mcts_arc2.llm.llm_builder import call_llm

def one(req):
   return call_llm('vllm_microsoft/Phi-4-mini-reasoning', 0.6, req)

messages = [{'role':'user','content':'Hello, return a short greeting.'}]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
   futures = [ex.submit(one, messages) for _ in range(4)]
   for f in concurrent.futures.as_completed(futures):
      print(f.result())
```

3. サーバ側とクライアント側のログを合わせて分析
  - サーバ側ログ（APIServer 出力）で `Running:` 数、`Avg generation throughput`、`Prefix cache hit rate` を見る。
  - クライアント側で並列数を増やした時に `Running` が増え、GPU%（nvidia-smi）や `Avg generation throughput` が上がるか確認する。

## run.py / call_llm に入れるデバッグログの具体例（変更案）

1. `src/ab_mcts_arc2/llm/llm_builder.py::call_llm` の冒頭に入れるログ

```python
def call_llm(model_name: str, model_temp: float, messages: list[dict]):
   print(f"[TRACE] call_llm: model={model_name} prompt_len={len(messages[0].get('content',''))} time={time.time()}")
   model = build_model(model_name)
   res = model.generate(messages, model_temp)
   print(f"[TRACE] model.generate returned: model={model_name} cost={res[1]}")
   return res
```

2. `experiments/arc2/run.py::generate_fn` の eval_results をファイル保存

```python
log_txt.write_text(json.dumps({'model': model_name, 'cost': cost, 'result': dataclasses.asdict(result), 'eval_results':[er.__dict__ for er in eval_results]}, indent=4))
```

これらは簡易で確実にトレースを取れる手法です。パフォーマンスに影響を与える可能性はありますが、デバッグ・測定用として短時間の導入は有効です。

## まとめ

- `run.py` は `generate_fn` を経由して `call_llm` を呼び、最終的に各モデルの `generate` が実行されます。
- ノード評価は `task.generate_eval_results` → `evaluate_code.eval_if_test_pass` のチェーンで隔離実行されます。
- vLLM の低スループットは同時リクエスト数、バッチング、プロンプト長やサーバ設定が主な要因であり、まずは並列リクエストを増やしてサーバ側の挙動を観察するのがおすすめです。

必要であれば、私の方で（1）`call_llm` にトレースログを追加するパッチ、（2）`generate_fn` に eval_results 保存を追加するパッチ、（3）簡易並列負荷テストスクリプトを追加して実行（私がテストを実行するには環境の制約があるのでユーザー側での実行手順を提示）を行います。どれを先にやりますか？
