import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from uuid import uuid4
from starlette.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database import AsyncSessionLocal, check_database_health
from app.main import app
from app.models.advanced import CodingChallenge
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.user import User, UserRole
from app.services.behavioral_service import BehavioralSTAREngine, OwnershipMetrics, STARBehavioralEvaluation
from app.services.code_sandbox import (
    CodeASTComplexityAnalyzer,
    IsolatedCodeSandbox,
    SandboxExecutionResult,
)
from app.services.system_design_service import (
    BuzzwordAnalysis,
    SystemDesignEngine,
    SystemDesignEvaluation,
)


# ─── 1. Unit Tests: Isolated Code Sandbox & AST ───────────────────────────────

async def test_code_sandbox_execution_and_public_hidden_tests():
    """Verify code execution in isolated subprocess with public and hidden test cases."""
    print("\n--- Testing Code Sandbox Execution & Hidden Test Masking ---")
    sandbox = IsolatedCodeSandbox(default_timeout_s=3.0)

    # Two Sum solution
    two_sum_code = """
def two_sum(nums, target):
    lookup = {}
    for idx, num in enumerate(nums):
        complement = target - num
        if complement in lookup:
            return [lookup[complement], idx]
        lookup[num] = idx
    return []
"""

    test_cases = [
        {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": [0, 1], "is_public": True},
        {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": [1, 2], "is_public": True},
        {"input": {"nums": [3, 3], "target": 6}, "expected_output": [0, 1], "is_public": False},  # Hidden
        {"input": {"nums": [-1, -2, -3, -4, -5], "target": -8}, "expected_output": [2, 4], "is_public": False},  # Hidden
    ]

    result: SandboxExecutionResult = await sandbox.execute(
        code=two_sum_code,
        test_cases=test_cases,
        entry_point="two_sum",
    )

    assert result.success is True, f"Execution failed: {result.error}"
    assert result.total_tests == 4
    assert result.passed_tests == 4
    assert result.failed_tests == 0
    assert result.pass_rate == 1.0
    assert result.security_passed is True

    # Validate hidden test case masking for client response
    client_dict = result.to_dict(mask_hidden=True)
    results_list = client_dict["test_results"]
    assert len(results_list) == 4

    # Public tests reveal actual inputs
    assert results_list[0]["is_public"] is True
    assert "[2, 7, 11, 15]" in results_list[0]["input_repr"]

    # Hidden tests mask raw input and expected output
    assert results_list[2]["is_public"] is False
    assert results_list[2]["input_repr"] == "[HIDDEN TEST CASE]"
    assert results_list[2]["expected_repr"] == "[HIDDEN TEST CASE]"
    assert results_list[2]["actual_repr"] == "[MATCHED]"

    print(f"[PASS] Two Sum sandbox: {result.passed_tests}/{result.total_tests} passed in {result.total_execution_time_ms:.1f}ms")
    print(f"[PASS] Hidden test cases correctly masked: {results_list[2]['input_repr']}")


async def test_code_sandbox_security_rejection():
    """Verify security validator blocks dangerous imports and system calls before execution."""
    print("\n--- Testing Sandbox Security Policy Enforcement ---")
    sandbox = IsolatedCodeSandbox()

    malicious_snippets = [
        ("import os\nos.system('dir')", "forbidden module 'os'"),
        ("import subprocess\nsubprocess.run(['ls'])", "forbidden module 'subprocess'"),
        ("import socket\ns = socket.socket()", "forbidden module 'socket'"),
        ("def hack():\n    eval('1+1')", "dangerous function 'eval()'"),
    ]

    for code, expected_kw in malicious_snippets:
        res = await sandbox.execute(code, [{"input": None, "expected_output": None}])
        assert res.security_passed is False, f"Expected security violation for: {code}"
        assert "Security Policy Violation" in res.error
        assert expected_kw in res.error
        print(f"[PASS] Successfully blocked malicious pattern: {expected_kw}")


async def test_code_sandbox_infinite_loop_timeout():
    """Verify strict execution timeout protects against infinite loops and DoS."""
    print("\n--- Testing Sandbox Execution Timeout (Infinite Loop Protection) ---")
    sandbox = IsolatedCodeSandbox(default_timeout_s=1.0)

    infinite_loop_code = """
def solution(n):
    total = 0
    while True:
        total += 1
    return total
"""
    res = await sandbox.execute(
        code=infinite_loop_code,
        test_cases=[{"input": 10, "expected_output": 10, "is_public": True}],
        entry_point="solution",
        timeout_s=1.0,
    )

    assert res.success is False
    assert "TimeLimitExceeded" in res.error
    assert res.total_execution_time_ms >= 900.0  # Spent ~1000ms before kill
    print(f"[PASS] Infinite loop aborted cleanly within timeout: {res.error}")


def test_static_ast_complexity_analyzer():
    """Verify AST complexity analyzer detects loop depth, cyclomatic complexity, and Big-O."""
    print("\n--- Testing Static AST Code Complexity Analyzer ---")
    analyzer = CodeASTComplexityAnalyzer()

    # O(1) Constant
    o1_code = "def get_first(arr):\n    return arr[0] if arr else None\n"
    m1 = analyzer.analyze(o1_code)
    assert "O(1)" in m1.estimated_time_complexity
    assert m1.loop_depth == 0

    # O(n) Linear
    on_code = "def find_max(arr):\n    m = arr[0]\n    for x in arr:\n        if x > m: m = x\n    return m\n"
    m2 = analyzer.analyze(on_code)
    assert "O(n)" in m2.estimated_time_complexity
    assert m2.loop_depth == 1

    # O(n^2) Quadratic
    on2_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"""
    m3 = analyzer.analyze(on2_code)
    assert "O(n^2)" in m3.estimated_time_complexity
    assert m3.loop_depth == 2
    assert any("nested loops" in s.lower() for s in m3.suggestions)

    print(f"[PASS] O(1) detected: {m1.estimated_time_complexity}")
    print(f"[PASS] O(n) detected: {m2.estimated_time_complexity}")
    print(f"[PASS] O(n^2) detected: {m3.estimated_time_complexity} with suggestions: {m3.suggestions[0]}")


# ─── 2. Unit Tests: System Design & Anti-Buzzword Engine ─────────────────────

async def test_system_design_evaluation_and_buzzword_defense():
    """Verify System Design engine: 8-pillar scoring and anti-buzzword defense."""
    print("\n--- Testing System Design Engine & Anti-Buzzword Detection ---")
    engine = SystemDesignEngine()

    # 1. Test Anti-Buzzword Filter on an unjustified buzzword-dropping answer
    buzzword_heavy_text = (
        "We will use Kafka for messaging, Cassandra for database, and Kubernetes for microservices. "
        "We will also throw in Redis for caching and Elasticsearch for search."
    )
    buzz_analysis: BuzzwordAnalysis = engine.inspect_buzzwords(buzzword_heavy_text)

    assert buzz_analysis.total_buzzwords_detected >= 4
    assert len(buzz_analysis.unjustified_buzzwords) >= 3
    assert buzz_analysis.penalty_applied > 0.0
    print(f"[PASS] Detected {buzz_analysis.total_buzzwords_detected} buzzwords, {len(buzz_analysis.unjustified_buzzwords)} unjustified. Penalty: -{buzz_analysis.penalty_applied} points.")

    # 2. Test Justified architecture answer
    justified_text = (
        "We implement an API Gateway layer with Envoy for rate limiting (Token Bucket algorithm). "
        "For the notification pipeline, we use Kafka partitioned by user_id to preserve message ordering, "
        "with a consumer group scaling based on consumer lag metrics. For metadata storage, PostgreSQL handles user accounts "
        "with read replicas in multi-AZ. Redis is used as a cache-aside layer with a 5-minute TTL and LRU eviction "
        "to reduce DB read latency below 2ms. For resilience, we deploy circuit breakers with fallback queues."
    )
    justified_analysis: BuzzwordAnalysis = engine.inspect_buzzwords(justified_text)
    assert len(justified_analysis.justified_buzzwords) >= 2
    assert "kafka" in justified_analysis.justified_buzzwords
    assert "redis" in justified_analysis.justified_buzzwords
    print(f"[PASS] Justified buzzwords validated: {justified_analysis.justified_buzzwords}")

    # 3. Full Evaluation of architecture
    eval_res: SystemDesignEvaluation = await engine.evaluate_architecture(
        problem_title="Distributed Rate Limiter",
        problem_prompt="Design a 500k RPS global rate limiter with sub-2ms latency",
        candidate_submission={
            "requirements": "Support 500k RPS with configurable sliding window counter quotas per API key.",
            "non_functional": "p99 latency < 2ms, 99.999% availability, graceful degradation on network partition.",
            "high_level": "Global API Gateway -> Local Redis Cluster -> Async PostgreSQL batch logger.",
            "data_model": "Hash structure in Redis with key 'ratelimit:{api_key}:{window_minute}' and integer counter.",
            "api_design": "POST /v1/consume {api_key, tokens} returning 200 OK or 429 Too Many Requests with Retry-After header.",
            "scalability": "Consistent hashing across Redis nodes, local memory token bucket caching to avoid network round-trip on every request.",
            "resilience": "Circuit breaker fallback: if Redis cluster is partitioned, fail-open with conservative local process quota.",
            "trade_offs": "Trade-off between strict global accuracy and latency: local memory caching allows sub-1ms response at the expense of temporary quota burst tolerance.",
        }
    )

    assert eval_res.overall_score >= 65.0
    assert len(eval_res.pillar_scores) == 8
    assert "requirements_clarification" in eval_res.pillar_scores
    assert "non_functional_requirements" in eval_res.pillar_scores
    assert "scalability_and_partitioning" in eval_res.pillar_scores
    print(f"[PASS] System Design overall score: {eval_res.overall_score} ({eval_res.tier}) across 8 pillars.")


# ─── 3. Unit Tests: Behavioral STAR & Ownership Audit ────────────────────────

async def test_behavioral_star_method_and_ownership_audit():
    """Verify STAR decomposition, 'I' vs 'We' ownership ratio, and metric extraction."""
    print("\n--- Testing Behavioral STAR Evaluator & Ownership Audit ---")
    engine = BehavioralSTAREngine()

    # 1. High ownership + Quantified metric answer
    strong_star_answer = (
        "In our core payment gateway, we experienced intermittent 504 timeouts causing transaction dropouts. "
        "My task as the lead infrastructure engineer was to identify the root cause and restore 99.99% availability within 48 hours. "
        "I analyzed connection pool metrics and discovered TCP socket exhaustion under peak thread load. "
        "I refactored the connection lifecycle, I implemented connection pooling with keep-alive, and I deployed circuit breakers. "
        "As a result, I reduced p99 latency from 450ms down to 32ms, I eliminated socket timeouts entirely, "
        "and I saved approximately $120,000 in lost transaction volume over the following quarter."
    )

    ownership: OwnershipMetrics = engine.analyze_ownership(strong_star_answer)
    assert ownership.ownership_level == "High Individual Ownership"
    assert ownership.i_we_ratio >= 0.60
    assert ownership.i_count >= 5
    print(f"[PASS] Ownership analysis: {ownership.ownership_level} (I/We ratio: {ownership.i_we_ratio:.2f})")

    metrics_found = engine.extract_quantifiable_metrics(strong_star_answer)
    assert any("99.99%" in m for m in metrics_found)
    assert any("48" in m for m in metrics_found)
    assert any("32ms" in m or "450ms" in m for m in metrics_found)
    assert any("120" in m or "120k" in m or "120000" in m for m in metrics_found)
    print(f"[PASS] Quantifiable metrics extracted: {metrics_found}")

    flags = engine.detect_flags(strong_star_answer, ownership, metrics_found)
    assert len(flags) == 0, f"Unexpected flags for strong answer: {[f.flag_type for f in flags]}"
    print("[PASS] Zero anti-pattern flags for strong STAR answer.")

    # 2. Passive / Vague answer test
    vague_answer = (
        "We had some database issues at work. We talked about it in our standup and we decided to upgrade the server. "
        "We worked together to fix it, and in the end things were much better and everyone was happy."
    )
    vague_ownership = engine.analyze_ownership(vague_answer)
    assert vague_ownership.ownership_level == "Passive/Ambiguous Team Attribution"
    vague_metrics = engine.extract_quantifiable_metrics(vague_answer)
    assert len(vague_metrics) == 0
    vague_flags = engine.detect_flags(vague_answer, vague_ownership, vague_metrics)
    flag_types = [f.flag_type for f in vague_flags]
    assert "MISSING_QUANTIFIABLE_RESULTS" in flag_types
    assert "PASSIVE_TEAM_OBSCURITY" in flag_types
    print(f"[PASS] Vague answer flagged correctly: {flag_types}")

    # 3. Full STAR Evaluation
    eval_res: STARBehavioralEvaluation = await engine.evaluate_star_answer(
        question="Tell me about a time you fixed a critical production outage.",
        answer_transcript=strong_star_answer,
        competency="ownership",
    )
    assert eval_res.overall_score >= 70.0
    assert "Situation" in eval_res.star_breakdown["situation"].name
    assert "Task" in eval_res.star_breakdown["task"].name
    assert "Action" in eval_res.star_breakdown["action"].name
    assert "Result" in eval_res.star_breakdown["result"].name
    assert eval_res.bar_raiser_verdict in ("Strong Hire", "Hire")
    print(f"[PASS] Full STAR evaluation complete: Score={eval_res.overall_score}, Verdict={eval_res.bar_raiser_verdict}")


# ─── 4. Integration Tests: API Endpoints via TestClient ───────────────────────

def test_specialized_interview_api_endpoints():
    """Verify HTTP API endpoints for Coding, System Design, and Behavioral interviews."""
    print("\n--- Testing HTTP API Endpoints (Coding, System Design, Behavioral) ---")
    user_id = uuid4()
    session_id = uuid4()

    async def _seed():
        db_ok = await check_database_health()
        if not db_ok:
            return False
        async with AsyncSessionLocal() as session:
            user = User(
                id=user_id,
                email=f"phase7-candidate-{uuid4().hex[:6]}@example.com",
                full_name="Jordan Specialized",
                hashed_password=hash_password("Pass1234!"),
                role=UserRole.candidate,
            )
            session.add(user)

            interview_sess = InterviewSession(
                id=session_id,
                user_id=user_id,
                target_question_count=5,
                current_difficulty=QuestionDifficulty.medium,
                status=SessionStatus.active,
            )
            session.add(interview_sess)
            await session.commit()
        from app.database import engine
        await engine.dispose()
        return True

    seeded = asyncio.run(_seed())
    if not seeded:
        print("[SKIP] PostgreSQL not connected in this test run.")
        return

    token = create_access_token(user_id=user_id, role="candidate")
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        # ── 1. Coding Endpoints ───────────────────────────────────────────────
        # Generate Challenge
        gen_resp = client.post(
            "/api/v1/coding/generate",
            json={"session_id": str(session_id), "difficulty": "medium", "language": "python"},
            headers=headers,
        )
        assert gen_resp.status_code == 201
        challenge_data = gen_resp.json()
        challenge_id = challenge_data["challenge_id"]
        assert len(challenge_data["test_cases"]) > 0
        print(f"[PASS] POST /api/v1/coding/generate: Challenge '{challenge_data['title']}' created.")

        # Run Tests (Visible Only)
        valid_code = (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, num in enumerate(nums):\n"
            "        if target - num in seen: return [seen[target - num], i]\n"
            "        seen[num] = i\n"
            "    return []\n"
        )
        run_resp = client.post(
            "/api/v1/coding/run-tests",
            json={"challenge_id": challenge_id, "code": valid_code, "language": "python"},
            headers=headers,
        )
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["security_passed"] is True
        assert run_data["total_tests"] > 0
        print(f"[PASS] POST /api/v1/coding/run-tests: Ran {run_data['total_tests']} public test(s).")

        # Submit Code (Runs Visible + Hidden Tests + Static AST + LLM Review)
        submit_resp = client.post(
            "/api/v1/coding/submit",
            json={"challenge_id": challenge_id, "code": valid_code, "language": "python"},
            headers=headers,
        )
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["score"] > 0.0
        assert "static_analysis" in submit_data
        assert "readability_score" in submit_data
        print(f"[PASS] POST /api/v1/coding/submit: Score {submit_data['score']} (Pass rate: {submit_data['pass_rate']}%)")

        # ── 2. System Design Endpoints ────────────────────────────────────────
        # Get Pillars
        pillars_resp = client.get("/api/v1/system-design/pillars", headers=headers)
        assert pillars_resp.status_code == 200
        assert len(pillars_resp.json()["pillars"]) == 8
        print(f"[PASS] GET /api/v1/system-design/pillars: Returned {len(pillars_resp.json()['pillars'])} architectural pillars.")

        # Create Challenge Scenario
        sd_challenge_resp = client.post(
            "/api/v1/system-design/challenge",
            json={"session_id": str(session_id), "scenario_key": "distributed_rate_limiter"},
            headers=headers,
        )
        assert sd_challenge_resp.status_code == 201
        sd_data = sd_challenge_resp.json()
        assert "Distributed Rate Limiter" in sd_data["title"]
        print(f"[PASS] POST /api/v1/system-design/challenge: Created '{sd_data['title']}'")

        # Evaluate System Design Submission
        sd_eval_resp = client.post(
            "/api/v1/system-design/evaluate",
            json={
                "session_id": str(session_id),
                "problem_title": sd_data["title"],
                "problem_prompt": sd_data["prompt"],
                "architecture_sections": {
                    "requirements": "Handle 500,000 QPS with sub-2ms latency for rate limiting API calls.",
                    "architecture": "Edge Envoy proxy with local token bucket cache, fallback to Redis cluster partitioned with consistent hashing.",
                    "tradeoffs": "Consistency vs latency: we allow a 1% over-limit burst during network partitions to guarantee availability.",
                },
            },
            headers=headers,
        )
        assert sd_eval_resp.status_code == 200
        sd_eval_data = sd_eval_resp.json()
        assert sd_eval_data["overall_score"] > 0
        assert "buzzword_analysis" in sd_eval_data
        print(f"[PASS] POST /api/v1/system-design/evaluate: Overall score {sd_eval_data['overall_score']} ({sd_eval_data['tier']})")

        # ── 3. Behavioral Endpoints ───────────────────────────────────────────
        # List Questions
        bq_resp = client.get("/api/v1/behavioral/questions?competency=ownership", headers=headers)
        assert bq_resp.status_code == 200
        b_questions = bq_resp.json()
        assert len(b_questions) > 0
        print(f"[PASS] GET /api/v1/behavioral/questions: Retrieved {len(b_questions)} ownership questions.")

        # Evaluate STAR
        star_resp = client.post(
            "/api/v1/behavioral/evaluate-star",
            json={
                "session_id": str(session_id),
                "question": b_questions[0]["question"],
                "answer_transcript": (
                    "My task as the lead engineer was to optimize database query latency. "
                    "I profiled the slow queries, I created composite B-tree indexes, and I optimized connection pooling. "
                    "As a result, I reduced query latency by 45% and improved throughput from 1,200 to 3,500 RPS."
                ),
                "competency": "ownership",
            },
            headers=headers,
        )
        assert star_resp.status_code == 200
        star_data = star_resp.json()
        assert star_data["overall_score"] > 0
        assert star_data["ownership_metrics"]["ownership_level"] == "High Individual Ownership"
        assert len(star_data["quantifiable_metrics_found"]) >= 2
        print(f"[PASS] POST /api/v1/behavioral/evaluate-star: Score {star_data['overall_score']} (Verdict: {star_data['bar_raiser_verdict']})")


def run_all():
    print("=== RUNNING PHASE 7 SPECIALIZED INTERVIEW ENGINES TESTS ===")
    asyncio.run(test_code_sandbox_execution_and_public_hidden_tests())
    asyncio.run(test_code_sandbox_security_rejection())
    asyncio.run(test_code_sandbox_infinite_loop_timeout())
    test_static_ast_complexity_analyzer()
    asyncio.run(test_system_design_evaluation_and_buzzword_defense())
    asyncio.run(test_behavioral_star_method_and_ownership_audit())
    test_specialized_interview_api_endpoints()
    print("=== ALL PHASE 7 SPECIALIZED INTERVIEW ENGINES TESTS PASSED ===")


if __name__ == "__main__":
    run_all()
