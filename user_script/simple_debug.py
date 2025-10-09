#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "hydra-core",
#     "python-dotenv",
#     "treequest",
# ]
# ///
"""
最もシンプルなデバッグスクリプト - 1ステップだけ実行

このスクリプトは:
- 1ステップ（ルートノードの生成）のみを実行
- 詳細なログを出力
- プロンプトと生成結果を完全に表示
"""

import sys
from pathlib import Path

# プロジェクトのルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "experiments" / "arc2"))
sys.path.insert(0, str(project_root / "src"))

import json
import time

from dotenv import load_dotenv

from ab_mcts_arc2.llm.llm_builder import call_llm
from ab_mcts_arc2.llm_generation_interface import GenerationRequest, GenerationResult
from ab_mcts_arc2.prompts.prompt_configs import PromptConfig
from ab_mcts_arc2.tasks.arc.task import ARCProblem
from prompt import BaselinePrompt


def main():
    """1ステップだけ実行して動作を確認"""

    # .envファイルの読み込み
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")

    # 設定
    task_id = "007bbfb7"  # 最初のタスク
    model_name = "o4-mini-2025-04-16"  # 使用するモデル
    temperature = 0.6

    print("\n" + "=" * 80)
    print("🔍 Simple Debug - Single Step Execution")
    print("=" * 80)
    print(f"Task ID: {task_id}")
    print(f"Model: {model_name}")
    print(f"Temperature: {temperature}")
    print("=" * 80)

    # タスクの読み込み
    arc_problem_path = project_root / f"ARC-AGI-2/data/evaluation/{task_id}.json"
    if not arc_problem_path.exists():
        print(f"\n❌ Task file not found: {arc_problem_path}")
        print("Available tasks:")
        eval_dir = project_root / "ARC-AGI-2/data/evaluation"
        if eval_dir.exists():
            tasks = sorted([f.stem for f in eval_dir.glob("*.json")])[:10]
            for t in tasks:
                print(f"  - {t}")
        sys.exit(1)

    print(f"\n📂 Loading task...")
    task = ARCProblem.load_file(arc_problem_path)
    print(f"✅ Task loaded:")
    print(f"   - Training examples (demos): {len(task.demos)}")
    print(f"   - Test examples: {len(task.tests)}")

    # デモの内容を表示
    print(f"\n📊 Demo example shapes:")
    for i, demo in enumerate(task.demos):
        print(f"   Demo {i}: input={demo.input.shape}, output={demo.output.shape}")

    # プロンプトテンプレートの作成
    print(f"\n📝 Creating prompt template...")
    prompt_template = BaselinePrompt(prompt_config=PromptConfig(), problem=task)
    print(f"✅ Prompt template created")

    # 初期プロンプトの生成
    print(f"\n📨 Generating initial prompt...")
    initial_prompt = prompt_template.initial_prompt()
    print(f"✅ Initial prompt generated ({len(initial_prompt)} characters)")

    # プロンプトの内容を表示
    print(f"\n" + "=" * 80)
    print("📄 FULL INITIAL PROMPT:")
    print("=" * 80)
    print(initial_prompt)
    print("=" * 80)

    # LLM呼び出し
    messages = [{"role": "user", "content": initial_prompt}]

    print(f"\n🤖 Calling LLM: {model_name}...")
    start_time = time.time()

    try:
        generation, cost = call_llm(model_name, temperature, messages)
        llm_time = time.time() - start_time

        print(f"✅ LLM response received!")
        print(f"   - Time: {llm_time:.2f}s")
        print(f"   - Cost: ${cost:.6f}")
        print(f"   - Length: {len(generation)} characters")

        # 生成結果を表示
        print(f"\n" + "=" * 80)
        print("📤 FULL LLM GENERATION:")
        print("=" * 80)
        print(generation)
        print("=" * 80)

        # GenerationResultの作成
        result = GenerationResult(
            request=GenerationRequest(messages=messages),
            generation=generation
        )

        # 評価
        print(f"\n🧪 Evaluating generated code...")
        eval_start = time.time()
        eval_results = task.generate_eval_results(llm_answer=result, kind="transform")
        eval_time = time.time() - eval_start

        print(f"✅ Evaluation completed in {eval_time:.2f}s")

        if eval_results is None:
            print(f"❌ Evaluation failed - no results")
            score = 0.0
        else:
            score = sum([eval_result.get_score() for eval_result in eval_results]) / len(eval_results)
            print(f"\n📊 Evaluation Results:")
            print(f"   - Overall Score: {score:.3f}")
            print(f"   - Number of examples: {len(eval_results)}")

            for i, eval_result in enumerate(eval_results):
                result_score = eval_result.get_score()
                status = "✅" if result_score > 0 else "❌"
                print(f"   {status} Example {i}: score={result_score:.3f}")

                # 詳細情報があれば表示
                if hasattr(eval_result, 'passed'):
                    print(f"      Passed: {eval_result.passed}")
                if hasattr(eval_result, 'error') and eval_result.error:
                    print(f"      Error: {eval_result.error}")

        # 結果を保存
        output_dir = project_root / "debug_output"
        output_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"simple_debug_{task_id}_{timestamp}.json"

        output_data = {
            "task_id": task_id,
            "model": model_name,
            "temperature": temperature,
            "prompt": initial_prompt,
            "generation": generation,
            "score": score,
            "cost": cost,
            "llm_time": llm_time,
            "eval_time": eval_time,
            "total_time": time.time() - start_time,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Results saved to: {output_file}")

        # サマリー
        print(f"\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Task: {task_id}")
        print(f"Model: {model_name}")
        print(f"Score: {score:.3f}")
        print(f"Cost: ${cost:.6f}")
        print(f"LLM Time: {llm_time:.2f}s")
        print(f"Eval Time: {eval_time:.2f}s")
        print(f"Total Time: {output_data['total_time']:.2f}s")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✨ Simple debug completed!")


if __name__ == "__main__":
    main()
