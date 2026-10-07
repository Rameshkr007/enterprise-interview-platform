#!/usr/bin/env python3
"""
Master Automated Regression Runner for Enterprise AI Mock Interview Platform.
Executes all 18 test suites in strict chronological phase order:
  Phase 1:  Foundation Architecture & Microservices DB (test_phase1_foundation.py)
  Phase 2:  Multi-Tenant Auth, RBAC & Organization Context (test_phase2_auth_rbac.py)
  Phase 3:  Resume Intelligence & PDF Parsing (test_phase3_resume_intelligence.py)
  Phase 4:  Semantic ATS 2.0 & Vector Matching Engine (test_phase4_semantic_ats.py)
  Phase 5:  Adaptive LangGraph Interview Engine (test_phase5_interview_engine.py)
  Phase 6:  Real-Time Audio DSP & Streaming Transcription (test_phase6_realtime_audio.py)
  Phase 7:  Specialized Interview Engines & AST Sandbox (test_phase7_specialized_interviews.py)
  Phase 8:  Candidate Twin, Learning Engine & Recruiter Copilot (test_phase8_twin_learning_recruiter.py)
  Phase 9:  Observability, AI Governance & Fault Resilience (test_phase9_observability_governance_resilience.py)
  Phase 10: Fullstack E2E Integration Suite (test_phase10_fullstack_e2e.py)
  Phase 11: System Design Canvas & Behavioral STAR+L (test_phase11_system_design_behavioral.py)
  Phase 12: Skill Graph DAG & Transitive Prerequisite Inference (test_phase12_skill_graph_dag.py)
  Phase 13: Personalized Learning & SuperMemo-2 Spaced Repetition (test_phase13_sm2_learning.py)
  Phase 14: Longitudinal Candidate AI Twin & Explainable AI (test_phase14_candidate_twin.py)
  Phase 15: Recruiter AI Copilot, Talent Pool & Bar-Raiser Debrief (test_phase15_recruiter_copilot.py)
  Phase 16: Enterprise Analytics, Distributed Tracing & SRE Incidents (test_phase16_analytics_observability.py)
  Phase 17: Zero-Trust Security, Reversible PII Vault & Prompt Guard (test_phase17_security_rate_limiting.py)
  Phase 18: End-to-End Testing Suites & Master Regression Orchestration (test_phase18_master_e2e_suites.py)
  Phase 19: Performance Profiling & Caching (test_phase19_performance_caching.py)
  Phase 20: Production Packaging & Deployment Orchestration (test_phase20_production_deployment.py)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent
TESTS_DIR = BASE_DIR / "tests"
RESULTS_FILE = TESTS_DIR / "regression_results.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TEST_SUITES = [
    {
        "phase": 1,
        "name": "Phase 1: Foundation Architecture & Microservices DB",
        "file": "test_phase1_foundation.py",
        "description": "Validates database connectivity, pgvector extension, connection pooling, and baseline schema.",
    },
    {
        "phase": 2,
        "name": "Phase 2: Multi-Tenant Auth, RBAC & Organization Context",
        "file": "test_phase2_auth_rbac.py",
        "description": "Validates multi-tenant isolation, user registration, JWT lifecycle, and role-based permissions.",
    },
    {
        "phase": 3,
        "name": "Phase 3: Resume Intelligence & PDF Parsing",
        "file": "test_phase3_resume_intelligence.py",
        "description": "Validates PDF/DOCX multi-format extraction, section categorization, and text normalization.",
    },
    {
        "phase": 4,
        "name": "Phase 4: Semantic ATS 2.0 & Vector Matching Engine",
        "file": "test_phase4_semantic_ats.py",
        "description": "Validates pgvector cosine similarity, skill gap detection, match tiers, and job description alignment.",
    },
    {
        "phase": 5,
        "name": "Phase 5: Adaptive LangGraph Interview Engine",
        "file": "test_phase5_interview_engine.py",
        "description": "Validates stateful state machine graph, topic routing, difficulty adaptation, and turn evaluations.",
    },
    {
        "phase": 6,
        "name": "Phase 6: Real-Time Audio DSP & Streaming Transcription",
        "file": "test_phase6_realtime_audio.py",
        "description": "Validates pyin pitch extraction, RMS silence detection, filler word analysis, and Whisper STT.",
    },
    {
        "phase": 7,
        "name": "Phase 7: Specialized Interview Engines & AST Sandbox",
        "file": "test_phase7_specialized_interviews.py",
        "description": "Validates sandboxed subprocess execution, AST security analysis, anti-buzzword scoring, and STAR.",
    },
    {
        "phase": 8,
        "name": "Phase 8: Candidate Twin, Learning Engine & Recruiter Copilot",
        "file": "test_phase8_twin_learning_recruiter.py",
        "description": "Validates baseline candidate twin aggregation, milestone learning plans, and recruiter requisition workflows.",
    },
    {
        "phase": 9,
        "name": "Phase 9: Observability, AI Governance & Fault Resilience",
        "file": "test_phase9_observability_governance_resilience.py",
        "description": "Validates Prometheus metrics exporter, circuit breakers, fallback degradation, and AI bias auditing.",
    },
    {
        "phase": 10,
        "name": "Phase 10: Fullstack E2E Integration Suite",
        "file": "test_phase10_fullstack_e2e.py",
        "description": "Validates complete candidate lifecycle from upload through assessment, reporting, and dashboard analytics.",
    },
    {
        "phase": 11,
        "name": "Phase 11: System Design Canvas & Behavioral STAR+L",
        "file": "test_phase11_system_design_behavioral.py",
        "description": "Validates 8-pillar architectural evaluation, anti-buzzword penalty engine, and STAR+L ownership ratio.",
    },
    {
        "phase": 12,
        "name": "Phase 12: Skill Graph DAG & Transitive Prerequisite Inference",
        "file": "test_phase12_skill_graph_dag.py",
        "description": "Validates Kahn's topological sorting, 3-color cycle detection, transitive credit decay, and root-cause gaps.",
    },
    {
        "phase": 13,
        "name": "Phase 13: Personalized Learning & SuperMemo-2 Spaced Repetition",
        "file": "test_phase13_sm2_learning.py",
        "description": "Validates mathematical SM-2 interval calculations, Ebbinghaus decay curve, flashcard deck seeding, and review sync.",
    },
    {
        "phase": 14,
        "name": "Phase 14: Longitudinal Candidate AI Twin & Explainable AI",
        "file": "test_phase14_candidate_twin.py",
        "description": "Validates multi-session synthesis, OLS growth velocity, Gaussian peer benchmarks, and grounded score transparency.",
    },
    {
        "phase": 15,
        "name": "Phase 15: Recruiter AI Copilot, Talent Pool & Bar-Raiser Debrief",
        "file": "test_phase15_recruiter_copilot.py",
        "description": "Validates dynamic rubric weighting, talent pool search, requisition calibration, and Bar-Raiser Debrief Memo.",
    },
    {
        "phase": 16,
        "name": "Phase 16: Enterprise Analytics, Distributed Tracing & SRE Incidents",
        "file": "test_phase16_analytics_observability.py",
        "description": "Validates organization talent supply vs demand, platform ROI, W3C correlation ID tracing, and active SRE alerting.",
    },
    {
        "phase": 17,
        "name": "Phase 17: Zero-Trust Security, Reversible PII Vault & Prompt Guard",
        "file": "test_phase17_security_rate_limiting.py",
        "description": "Validates Fernet AES-256 PII vault, 8 prompt injection signatures, cryptographic audit ledger, and sensitive rate limits.",
    },
    {
        "phase": 18,
        "name": "Phase 18: End-to-End Testing Suites & Master Regression Orchestration",
        "file": "test_phase18_master_e2e_suites.py",
        "description": "Validates unified 14-step cross-subsystem Master E2E enterprise lifecycle covering all platform capabilities.",
    },
    {
        "phase": 19,
        "name": "Phase 19: Performance Profiling & Caching",
        "file": "test_phase19_performance_caching.py",
        "description": "Validates L1/L2 hierarchical caching, SQL slow query & N+1 detection, W3C Server-Timing, and synthetic benchmarks.",
    },
    {
        "phase": 20,
        "name": "Phase 20: Production Packaging & Deployment Orchestration",
        "file": "test_phase20_production_deployment.py",
        "description": "Validates multi-container production orchestrator, environment configuration audit, migrations DAG, and deployment readiness.",
    },
]


def run_suite(suite_info: dict) -> dict:
    test_file = TESTS_DIR / suite_info["file"]
    suite_name = suite_info["name"]
    print(f"\n================================================================================")
    print(f"[RUN] EXECUTING: {suite_name}")
    print(f"  File: {test_file.name}")
    print(f"  Scope: {suite_info['description']}")
    print(f"================================================================================")

    # Clear rate limit state between suites to prevent sliding window bleed
    try:
        import redis
        r = redis.Redis()
        rl_keys = r.keys("ratelimit:*")
        if rl_keys:
            r.delete(*rl_keys)
    except Exception:
        pass

    start_time = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-u", str(test_file)],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    stdout_lines = []
    if proc.stdout:
        for line in iter(proc.stdout.readline, ""):
            print(line, end="")
            stdout_lines.append(line)
        proc.stdout.close()

    proc.wait()
    duration = round(time.perf_counter() - start_time, 2)
    passed = (proc.returncode == 0)

    status_badge = "[PASS] 100%" if passed else f"[FAIL] (Exit {proc.returncode})"
    print(f"\n---> RESULT: {suite_name} => {status_badge} in {duration}s\n")

    return {
        "phase": suite_info["phase"],
        "name": suite_info["name"],
        "file": suite_info["file"],
        "description": suite_info["description"],
        "passed": passed,
        "exit_code": proc.returncode,
        "duration_seconds": duration,
        "timestamp": datetime.now(UTC).isoformat(),
        "log_snippet": "".join(stdout_lines[-20:]) if stdout_lines else "",
    }


def main() -> int:
    overall_start = time.perf_counter()
    print("=" * 80)
    print("      ENTERPRISE PLATFORM MASTER AUTOMATED REGRESSION RUNNER")
    print(f"      Executing all {len(TEST_SUITES)} Enterprise Test Suites Sequentially")
    print(f"      Started At: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    results = []
    total_passed = 0
    total_failed = 0

    for suite in TEST_SUITES:
        res = run_suite(suite)
        results.append(res)
        if res["passed"]:
            total_passed += 1
        else:
            total_failed += 1
        time.sleep(0.5)

    total_duration = round(time.perf_counter() - overall_start, 2)
    pass_rate = round((total_passed / len(TEST_SUITES)) * 100, 1) if TEST_SUITES else 0.0

    summary_data = {
        "execution_timestamp": datetime.now(UTC).isoformat(),
        "total_suites": len(TEST_SUITES),
        "passed_suites": total_passed,
        "failed_suites": total_failed,
        "pass_rate_percentage": pass_rate,
        "total_duration_seconds": total_duration,
        "all_passed": total_failed == 0,
        "suites": results,
    }

    try:
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)
        print(f"\n[INFO] Comprehensive regression summary written to: {RESULTS_FILE}")
    except Exception as e:
        print(f"[WARN] Failed to write regression results JSON: {e}")

    # Output Final Summary Matrix Table
    print("\n" + "=" * 80)
    print("                      MASTER REGRESSION AUDIT SUMMARY")
    print("=" * 80)
    print(f"{'PHASE':<8} | {'STATUS':<10} | {'DURATION':<10} | {'SUITE NAME'}")
    print("-" * 80)
    for r in results:
        status_str = "PASS 100%" if r["passed"] else f"FAIL (c={r['exit_code']})"
        dur_str = f"{r['duration_seconds']:.2f}s"
        print(f"P{r['phase']:02d}      | {status_str:<10} | {dur_str:<10} | {r['name']}")
    print("-" * 80)
    print(f"TOTAL SUITES:    {len(TEST_SUITES)}")
    print(f"PASSED:          {total_passed}")
    print(f"FAILED:          {total_failed}")
    print(f"PASS RATE:       {pass_rate}%")
    print(f"TOTAL TIME:      {total_duration:.2f} seconds ({total_duration/60:.2f} mins)")
    print("=" * 80)

    if total_failed == 0:
        print("\n>>> SUCCESS: 100% REGRESSION PASS RATE ACROSS ALL 18 ENTERPRISE SUITES! <<<\n")
        return 0
    else:
        print(f"\n>>> WARNING: {total_failed} SUITE(S) FAILED REGRESSION AUDIT. <<<\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
