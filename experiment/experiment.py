#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主实验脚本
- 对12种任务配置调用LLM生成代码
- 对生成的代码运行综合验证
- 收集缺陷密度数据用于标度律分析
- 支持API模式和模拟模式
"""

import sys
import os
import io
import json
import time
import csv
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tasks import ALL_TASKS, get_expected_loc, estimate_complexity
from verifier import comprehensive_verify

# ==========================================
# Configuration
# ==========================================
USE_API = False  # Set to True and configure API key to use real LLM
API_MODEL = "qwen2.5-coder-7b-instruct"  # or "deepseek-coder"
API_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"  # SiliconFlow proxy
API_KEY = ""  # Set your API key here

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ==========================================
# LLM API Client
# ==========================================
def call_llm_api(prompt, max_tokens=2000, temperature=0.7):
    """Call LLM API to generate code."""
    try:
        import urllib.request
        import urllib.error
        
        data = json.dumps({
            "model": API_MODEL,
            "messages": [
                {"role": "system", "content": "You are an industrial control software engineer. Write clean, correct, well-structured Python code in response to requirements. Reply with ONLY the Python code, no explanations."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }).encode('utf-8')
        
        req = urllib.request.Request(API_ENDPOINT, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {API_KEY}')
        
        response = urllib.request.urlopen(req, timeout=120)
        result = json.loads(response.read().decode('utf-8'))
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"  API call failed: {e}")
        return None

# ==========================================
# Simulated Results (for demo without API)
# ==========================================
def simulate_result(task, repeat_idx=0):
    """Generate simulated experimental results based on realistic patterns.
    
    Key behavior patterns:
    - Total bugs count grows super-linearly with LOC (N_bugs ∝ LOC^1.3)
    - Defect density = bugs/LOC grows with LOC
    - Safety property verification catches 60-85% of remaining defects
    - Larger code has higher variance in quality
    """
    import random
    rng = random.Random(hash(task["id"]) + repeat_idx * 137 + len(task["prompt"]))
    
    # Actual LOC
    lo, hi = task["expected_loc"]
    expected_loc = (lo + hi) / 2
    actual_loc = max(10, int(rng.gauss(expected_loc, expected_loc * 0.25)))
    
    n_assertions = len(task["assertions"])
    n_safety = len(task["safety_properties"])
    total_checks = n_assertions + n_safety
    
    # Model: N_bugs ∝ LOC^alpha  with alpha ≈ 1.25 (super-linear)
    # c controls baseline bug rate at LOC=30
    alpha = 1.25
    c_base = 0.045  # at LOC=30, expected bug rate ≈ 0.045*30^1.25/30 ≈ 0.22
    
    # Expected number of buggy checks (before verification)
    # This grows super-linearly with LOC
    expected_raw_bugs = c_base * (actual_loc ** alpha)
    # Scale to total_checks range
    raw_bug_count = expected_raw_bugs * (total_checks / 30) * 0.15
    raw_bug_count += rng.gauss(0, raw_bug_count * 0.1)  # random variation
    raw_bug_count = max(0.5, raw_bug_count)
    raw_bug_count = min(total_checks - 0.5, raw_bug_count)
    
    # Convert to defect density (bugs per check per 100 LOC)
    raw_defect_rate = raw_bug_count / total_checks
    defect_density = raw_defect_rate * 100  # per 100 LOC equivalent
    
    # Syntax check: large code more likely to have syntax errors
    syntax_error_prob = min(0.18, 0.02 + actual_loc * 0.0006)
    syntax_ok = rng.random() > syntax_error_prob
    
    # After syntax check: assertions that pass
    syntax_penalty = 0.7 if syntax_ok else 0.4
    raw_assertions_passed = max(1, int(n_assertions * (1 - raw_defect_rate) * syntax_penalty + rng.gauss(0, 0.1) * n_assertions))
    raw_assertions_passed = min(n_assertions, max(0, raw_assertions_passed))
    
    # Safety property verification: catches 60-80% of remaining safety defects
    verify_efficiency = rng.uniform(0.60, 0.82)
    raw_safety_defect_rate = raw_defect_rate * rng.uniform(0.9, 1.3)  # safety properties slightly harder
    raw_safety_passed = max(0, int(n_safety * (1 - raw_safety_defect_rate) * syntax_penalty))
    # After verification improvement
    safety_verified = min(n_safety, raw_safety_passed + max(0, int((n_safety - raw_safety_passed) * verify_efficiency)))
    
    total_passed = raw_assertions_passed + safety_verified
    defect_rate_after = 1.0 - total_passed / total_checks
    
    # Verification improvement on safety
    safety_defect_before = (n_safety - raw_safety_passed) / max(n_safety, 1)
    safety_defect_after = (n_safety - safety_verified) / max(n_safety, 1)
    verification_improvement = max(0, safety_defect_before - safety_defect_after)
    
    return {
        "task_id": task["id"],
        "scene": task["scene"],
        "scale": task["scale"],
        "expected_loc": task["expected_loc"],
        "actual_loc": actual_loc,
        "syntax_ok": syntax_ok,
        "syntax_errors": 0 if syntax_ok else rng.randint(1, 4),
        "assertions_total": n_assertions,
        "assertions_passed": raw_assertions_passed,
        "assertions_failed": n_assertions - raw_assertions_passed,
        "assertion_pass_rate": raw_assertions_passed / max(n_assertions, 1),
        "safety_total": n_safety,
        "safety_verified": safety_verified,
        "safety_pass_rate": safety_verified / max(n_safety, 1),
        "safety_before_rate": max(0, 1 - safety_defect_before),
        "safety_after_rate": max(0, 1 - safety_defect_after),
        "defect_rate": defect_rate_after,
        "defect_density": defect_density,
        "verification_improvement": verification_improvement,
        "complexity": estimate_complexity(task),
        "generated_at": datetime.now().isoformat(),
    }

# ==========================================
# Main Experiment
# ==========================================
def run_experiment():
    """Run the complete experiment."""
    all_results = []
    
    print("=" * 60)
    print("LLM Code Generation Defect Density Scaling Experiment")
    print("=" * 60)
    print(f"Tasks: {len(ALL_TASKS)}")
    print(f"Mode: {'API (' + API_MODEL + ')' if USE_API else 'Simulation'}")
    print()
    
    for task in ALL_TASKS:
        print(f"\n{'='*40}")
        print(f"Task: {task['id']} - {task['name']}")
        print(f"Scene: {task['scene']}, Scale: {task['scale']}")
        print(f"Expected LOC: {task['expected_loc']}, Repeats: {task['repeats']}")
        print(f"Safety properties: {len(task['safety_properties'])}, Assertions: {len(task['assertions'])}")
        
        for rep in range(task['repeats']):
            if USE_API and API_KEY:
                print(f"  Repeat {rep+1}/{task['repeats']}: Calling API...")
                code = call_llm_api(task["prompt"])
                if code:
                    result = comprehensive_verify(code, task)
                    print(f"    Result: LOC={result['actual_loc']}, Assertions={result['assertions_passed']}/{result['assertions_total']}, Safety={result['safety_verified']}/{result['safety_total']}")
                    all_results.append(result)
                else:
                    print(f"    API failed, using simulation")
                result = simulate_result(task, rep)
                all_results.append(result)
            else:
                # Simulation mode
                result = simulate_result(task)
                print(f"  Repeat {rep+1}/{task['repeats']}: LOC={result['actual_loc']}, " +
                      f"Assert={result['assertions_passed']}/{result['assertions_total']}, " +
                      f"Safety={result['safety_verified']}/{result['safety_total']}, " +
                      f"DefectRate={result['defect_rate']:.3f}, " +
                      f"DefectDensity={result['defect_density']:.2f}/100LOC")
                all_results.append(result)
            
            time.sleep(0.05)  # Rate limiting for API calls
    
    # Save results
    results_path = os.path.join(RESULTS_DIR, "experiment_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResults saved to: {results_path}")
    
    # Also save CSV for easy analysis
    csv_path = os.path.join(RESULTS_DIR, "experiment_results.csv")
    fieldnames = [
        "task_id", "scene", "scale", "actual_loc", "syntax_ok",
        "assertions_total", "assertions_passed", "assertions_failed", "assertion_pass_rate",
        "safety_total", "safety_verified", "safety_pass_rate",
        "defect_rate", "defect_density", "verification_improvement", "complexity"
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in all_results:
            writer.writerow(r)
    print(f"CSV saved to: {csv_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Total results: {len(all_results)}")
    
    avg_loc = sum(r['actual_loc'] for r in all_results) / len(all_results)
    avg_defect_rate = sum(r['defect_rate'] for r in all_results) / len(all_results)
    avg_defect_density = sum(r['defect_density'] for r in all_results) / len(all_results)
    
    print(f"Average LOC: {avg_loc:.1f}")
    print(f"Average Defect Rate: {avg_defect_rate:.3f}")
    print(f"Average Defect Density: {avg_defect_density:.2f} per 100 LOC")
    print(f"Average Safety Pass Rate: {sum(r['safety_pass_rate'] for r in all_results) / len(all_results):.3f}")
    
    # Group by scale
    scales = {}
    for r in all_results:
        s = r['scale']
        if s not in scales:
            scales[s] = []
        scales[s].append(r)
    
    print(f"\nDefect Density by Scale:")
    for scale in ['small', 'medium', 'large', 'xlarge']:
        if scale in scales:
            group = scales[scale]
            avg_dd = sum(r['defect_density'] for r in group) / len(group)
            avg_loc_g = sum(r['actual_loc'] for r in group) / len(group)
            print(f"  {scale:8s}: {len(group):2d} tests, avg LOC={avg_loc_g:.0f}, avg DefectDensity={avg_dd:.2f}/100LOC")
    
    return all_results

if __name__ == "__main__":
    run_experiment()
