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
アルゴリズムの動作を理解するためのデバッグスクリプト

特徴:
- ステップ数を5に制限
- 生成長を短く設定（max_tokens削減）
- 各ステップで詳細なログを出力
- プロンプトと生成結果を確認しやすく表示
"""

import sys
from pathlib import Path

# プロジェクトのルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "experiments" / "arc2"))
sys.path.insert(0, str(project_root / "src"))

import dataclasses
import json
import time
from functools import partial

import treequest as tq
from dotenv import load_dotenv

from ab_mcts_arc2.llm.llm_builder import call_llm
from ab_mcts_arc2.llm_generation_interface import GenerationRequest, GenerationResult
from ab_mcts_arc2.prompts.prompt_configs import PromptConfig
from ab_mcts_arc2.tasks.arc.task import ARCProblem
from prompt import BaselinePrompt
from utils import NodeState


def generate_fn_with_debug(
    state: NodeState | None,
    task: ARCProblem,
    prompt_template: BaselinePrompt,
    model_name: str,
    model_temp: float,
    step_num: int,
) -> tuple[NodeState, float]:
    """デバッグ情報を出力するgenerate_fn"""

    print("\n" + "=" * 80)
    print(f"🔍 STEP {step_num}: Generating node")
    print("=" * 80)

    start_time = time.time()

    # プロンプトの生成
    if state is None:
        print("📝 Initial node (root)")
        prompt_content = prompt_template.initial_prompt()
        messages = [{"role": "user", "content": prompt_content}]
        print(f"\n📨 Prompt length: {len(prompt_content)} characters")
        print(f"📨 Prompt preview (first 500 chars):\n{prompt_content[:500]}...")
    else:
        print(f"📝 Child node (parent model: {state.model_name})")
        feedback_prompt = prompt_template.feedback_prompt(
            "transform",
            eval_results=state.eval_results,
            generation_result=state.generation_result,
        )
        messages = [{"role": "user", "content": feedback_prompt}]
        print(f"\n📨 Feedback prompt length: {len(feedback_prompt)} characters")
        print(f"📨 Feedback prompt preview (first 500 chars):\n{feedback_prompt[:500]}...")

    # LLM呼び出し
    print(f"\n🤖 Calling LLM: {model_name} (temp={model_temp})")
    llm_start = time.time()
    generation, cost = call_llm(model_name, model_temp, messages)
    llm_time = time.time() - llm_start
    print(f"✅ LLM response received in {llm_time:.2f}s (cost: ${cost:.6f})")
    print(f"📤 Generation length: {len(generation)} characters")
    print(f"📤 Generation preview (first 500 chars):\n{generation[:500]}...")

    # GenerationResultの作成
    result = GenerationResult(
        request=GenerationRequest(messages=messages),
        generation=generation
    )

    # 評価
    print("\n🧪 Evaluating generated code...")
    eval_start = time.time()
    eval_results = task.generate_eval_results(llm_answer=result, kind="transform")
    eval_time = time.time() - eval_start

    if eval_results is None:
        score = 0.0
        print(f"❌ Evaluation failed (score: {score:.3f})")
    else:
        score = sum([eval_result.get_score() for eval_result in eval_results]) / len(eval_results)
        print(f"✅ Evaluation completed in {eval_time:.2f}s")
        print(f"📊 Score: {score:.3f}")
        print(f"📊 Evaluation details:")
        for i, eval_result in enumerate(eval_results):
            print(f"   - Example {i}: score={eval_result.get_score():.3f}")

    total_time = time.time() - start_time
    print(f"\n⏱️  Total node time: {total_time:.2f}s")
    print("=" * 80)

    return NodeState(
        generation_result=result,
        eval_results=eval_results,
        model_name=model_name
    ), score


def main():
    """メイン実行関数"""

    # .envファイルの読み込み
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")

    # 設定
    # 簡単なタスクを使用（task_id=0）
    task_id = "007bbfb7"  # ARC-AGI-2の最初のタスク
    max_steps = 5  # ステップ数を制限

    print("\n" + "=" * 80)
    print("🚀 AB-MCTS Algorithm Debug Script")
    print("=" * 80)
    print(f"Task ID: {task_id}")
    print(f"Max steps: {max_steps}")

    # タスクの読み込み
    arc_problem_path = project_root / f"ARC-AGI-2/data/evaluation/{task_id}.json"
    if not arc_problem_path.exists():
        print(f"❌ Task file not found: {arc_problem_path}")
        print("Please download ARC-AGI-2 data or use a different task_id")
        sys.exit(1)

    print(f"📂 Loading task from: {arc_problem_path}")
    task = ARCProblem.load_file(arc_problem_path)
    print(f"✅ Task loaded: {len(task.demos)} demos, {len(task.tests)} tests")

    # プロンプトテンプレートの作成
    prompt_template = BaselinePrompt(prompt_config=PromptConfig(), problem=task)

    # モデル設定（軽量なモデルを使用）
    # 環境に応じて変更してください
    model_config = {
        "name": "o4-mini-2025-04-16",  # 軽量なモデル
        "temperature": 0.6
    }

    print(f"🤖 Using model: {model_config['name']}")

    # アルゴリズムの初期化（ABMCTSA）
    algo = tq.ABMCTSA(model_selection_strategy="stack")
    print(f"📊 Algorithm: ABMCTSA (model_selection_strategy=stack)")

    # 探索木の初期化
    search_tree = algo.init_tree()
    print("✅ Search tree initialized")

    # generate_fn関数の準備
    step_counter = [0]  # クロージャで使えるようにリストを使用

    def make_generate_fn():
        def wrapper(state):
            step_counter[0] += 1
            return generate_fn_with_debug(
                state=state,
                task=task,
                prompt_template=prompt_template,
                model_name=model_config["name"],
                model_temp=model_config["temperature"],
                step_num=step_counter[0]
            )
        return wrapper

    generate_fns = {
        model_config["name"]: make_generate_fn()
    }

    # 探索ループ
    print("\n" + "=" * 80)
    print("🔄 Starting search loop")
    print("=" * 80)

    start_time = time.time()

    for i in range(max_steps):
        print(f"\n\n{'#' * 80}")
        print(f"# ITERATION {i + 1}/{max_steps}")
        print(f"{'#' * 80}\n")

        iter_start = time.time()
        search_tree = algo.step(search_tree, generate_fns)
        iter_time = time.time() - iter_start

        n_nodes = len(algo.get_state_score_pairs(search_tree))
        print(f"\n📈 Tree now has {n_nodes} nodes (iteration took {iter_time:.2f}s)")

        # ベストスコアの表示
        state_score_pairs = algo.get_state_score_pairs(search_tree)
        if state_score_pairs:
            best_score = max(score for _, score in state_score_pairs)
            print(f"🏆 Best score so far: {best_score:.3f}")

    total_time = time.time() - start_time

    # 最終結果のサマリー
    print("\n\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Total nodes created: {len(algo.get_state_score_pairs(search_tree))}")

    state_score_pairs = algo.get_state_score_pairs(search_tree)
    if state_score_pairs:
        best_state, best_score = max(state_score_pairs, key=lambda x: x[1])
        print(f"Best score achieved: {best_score:.3f}")
        print(f"Best model: {best_state.model_name}")

        # ベスト解の保存
        output_dir = project_root / "debug_output"
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f"debug_result_{task_id}.json"
        output_data = {
            "task_id": task_id,
            "best_score": best_score,
            "model": best_state.model_name,
            "generation": best_state.generation_result.generation,
            "total_time": total_time,
            "total_nodes": len(state_score_pairs)
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✅ Results saved to: {output_file}")

    print("\n" + "=" * 80)
    print("✨ Debug script completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
