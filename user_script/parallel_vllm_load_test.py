#!/usr/bin/env python3
"""
Simple parallel load tester for vLLM via call_llm in this repo.
Usage:
  python user_script/parallel_vllm_load_test.py --workers 4 --requests 40

The script will send `requests` total requests using a ThreadPoolExecutor
with `workers` concurrent workers. It measures per-request latency and
prints summary stats.
"""

import argparse
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from ab_mcts_arc2.llm.llm_builder import call_llm


def one_call(model_name, temp, messages):
    start = time.perf_counter()
    try:
        resp, cost = call_llm(model_name, temp, messages)
        ok = True
    except Exception as e:
        resp = None
        cost = None
        ok = False
        err = str(e)
    elapsed = time.perf_counter() - start
    return {
        "ok": ok,
        "elapsed": elapsed,
        "resp_len": len(resp) if resp else 0,
        "cost": cost,
        "err": err if not ok else None,
    }


def run_load_test(model_name, temp, messages, workers, requests):
    latencies = []
    resp_lens = []
    errors = 0
    start_all = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(one_call, model_name, temp, messages) for _ in range(requests)]
        for f in as_completed(futures):
            r = f.result()
            if r["ok"]:
                latencies.append(r["elapsed"])
                resp_lens.append(r["resp_len"])
            else:
                errors += 1
    total_time = time.perf_counter() - start_all
    done = len(latencies)
    print("--- load test summary ---")
    print(f"workers: {workers}, requests: {requests}")
    print(f"successful: {done}, errors: {errors}")
    if done:
        print(f"total wall time: {total_time:.3f}s")
        print(f"throughput (req/s): {requests/total_time:.3f}")
        print(f"median latency: {statistics.median(latencies):.3f}s")
        print(f"p95 latency: {statistics.quantiles(latencies, n=100)[94]:.3f}s")
        print(f"mean resp len: {statistics.mean(resp_lens):.1f} chars")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--requests', type=int, default=20)
    parser.add_argument('--model', type=str, default='vllm_microsoft/Phi-4-mini-reasoning')
    parser.add_argument('--temp', type=float, default=0.6)
    parser.add_argument('--prompt', type=str, default='Hello. Return a short greeting.')
    args = parser.parse_args()

    messages = [{"role": "user", "content": args.prompt}]

    run_load_test(args.model, args.temp, messages, args.workers, args.requests)
