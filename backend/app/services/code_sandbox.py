from __future__ import annotations

import ast
import asyncio
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import structlog

log = structlog.get_logger(__name__)

# Disallowed modules and built-ins for Python sandbox execution
DISALLOWED_MODULES = {
    "os", "sys", "subprocess", "socket", "pty", "shutil", "ctypes",
    "posix", "nt", "importlib", "signal", "multiprocessing", "threading",
    "http", "urllib", "requests", "aiohttp", "builtins"
}

DISALLOWED_CALLS = {
    "eval", "exec", "open", "__import__", "compile", "breakpoint"
}


class SandboxSecurityException(Exception):
    """Raised when code violates security policies (dangerous imports or system calls)."""
    pass


class SandboxTimeoutException(Exception):
    """Raised when code execution exceeds CPU/wall-clock time limit."""
    pass


@dataclass
class TestCaseResult:
    test_index: int
    is_public: bool
    passed: bool
    input_repr: str
    expected_repr: str
    actual_repr: str | None
    execution_time_ms: float
    error: str | None = None
    stdout: str = ""

    def to_dict(self, mask_hidden: bool = True) -> dict[str, Any]:
        """Format for client response. Masks inputs/outputs for hidden test cases if required."""
        if not self.is_public and mask_hidden:
            return {
                "test_index": self.test_index,
                "is_public": False,
                "passed": self.passed,
                "input_repr": "[HIDDEN TEST CASE]",
                "expected_repr": "[HIDDEN TEST CASE]",
                "actual_repr": "[HIDDEN]" if not self.passed else "[MATCHED]",
                "execution_time_ms": round(self.execution_time_ms, 2),
                "error": "Failed edge case assertion" if self.error and not self.passed else None,
                "stdout": "",
            }
        return {
            "test_index": self.test_index,
            "is_public": self.is_public,
            "passed": self.passed,
            "input_repr": self.input_repr,
            "expected_repr": self.expected_repr,
            "actual_repr": self.actual_repr,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "error": self.error,
            "stdout": self.stdout,
        }


@dataclass
class StaticAnalysisMetrics:
    estimated_time_complexity: str
    estimated_space_complexity: str
    cyclomatic_complexity: int
    lines_of_code: int
    loop_depth: int
    has_recursion: bool
    quality_score: float  # 0 to 100
    suggestions: list[str] = field(default_factory=list)


@dataclass
class SandboxExecutionResult:
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    total_execution_time_ms: float
    test_results: list[TestCaseResult]
    static_analysis: StaticAnalysisMetrics
    security_passed: bool
    error: str | None = None

    def to_dict(self, mask_hidden: bool = True) -> dict[str, Any]:
        return {
            "success": self.success,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": round(self.pass_rate, 2),
            "total_execution_time_ms": round(self.total_execution_time_ms, 2),
            "test_results": [r.to_dict(mask_hidden=mask_hidden) for r in self.test_results],
            "static_analysis": {
                "estimated_time_complexity": self.static_analysis.estimated_time_complexity,
                "estimated_space_complexity": self.static_analysis.estimated_space_complexity,
                "cyclomatic_complexity": self.static_analysis.cyclomatic_complexity,
                "lines_of_code": self.static_analysis.lines_of_code,
                "loop_depth": self.static_analysis.loop_depth,
                "has_recursion": self.static_analysis.has_recursion,
                "quality_score": round(self.static_analysis.quality_score, 1),
                "suggestions": self.static_analysis.suggestions,
            },
            "security_passed": self.security_passed,
            "error": self.error,
        }


class CodeSecurityValidator(ast.NodeVisitor):
    """Inspects Python Abstract Syntax Tree (AST) to prevent unauthorized system access."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_mod = alias.name.split(".")[0]
            if base_mod in DISALLOWED_MODULES:
                self.violations.append(f"Import of forbidden module '{alias.name}' is strictly prohibited.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod in DISALLOWED_MODULES:
                self.violations.append(f"Import from forbidden module '{node.module}' is strictly prohibited.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in DISALLOWED_CALLS:
                self.violations.append(f"Invoking dangerous function '{node.func.id}()' is disallowed.")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in {"system", "popen", "spawn", "exec", "eval"}:
                self.violations.append(f"Attribute access '{node.func.attr}()' is disallowed.")
        self.generic_visit(node)


class CodeASTComplexityAnalyzer:
    """Performs static code quality, cyclomatic complexity, and asymptotic Big-O estimation."""

    def analyze(self, code: str) -> StaticAnalysisMetrics:
        try:
            tree = ast.parse(code)
        except Exception as exc:
            return StaticAnalysisMetrics(
                estimated_time_complexity="Unknown (Syntax Error)",
                estimated_space_complexity="Unknown",
                cyclomatic_complexity=1,
                lines_of_code=len(code.splitlines()),
                loop_depth=0,
                has_recursion=False,
                quality_score=0.0,
                suggestions=[f"Fix syntax errors: {exc}"],
            )

        lines = [line.strip() for line in code.splitlines() if line.strip() and not line.strip().startswith("#")]
        loc = len(lines)

        max_loop_depth = 0
        current_loop_depth = 0
        branch_count = 1
        has_sort = False
        recursive_calls = False
        func_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_names.add(node.name)

        def walk_depth(n: ast.AST, depth: int) -> None:
            nonlocal max_loop_depth, branch_count, has_sort, recursive_calls
            is_loop = isinstance(n, (ast.For, ast.While))
            new_depth = depth + (1 if is_loop else 0)
            if new_depth > max_loop_depth:
                max_loop_depth = new_depth

            if isinstance(n, (ast.If, ast.ExceptHandler, ast.With, ast.Assert)):
                branch_count += 1

            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    if n.func.id in func_names:
                        recursive_calls = True
                    if n.func.id == "sorted":
                        has_sort = True
                elif isinstance(n.func, ast.Attribute):
                    if n.func.attr == "sort":
                        has_sort = True

            for child in ast.iter_child_nodes(n):
                walk_depth(child, new_depth)

        walk_depth(tree, 0)

        # Estimate Time Complexity
        if max_loop_depth == 0:
            if recursive_calls:
                time_complexity = "O(2^n) or O(n) [Recursive]"
            else:
                time_complexity = "O(1) [Constant Time]"
        elif max_loop_depth == 1:
            if has_sort:
                time_complexity = "O(n log n) [Single Loop with Sorting]"
            else:
                time_complexity = "O(n) [Linear Time]"
        elif max_loop_depth == 2:
            time_complexity = "O(n^2) [Quadratic Time - Nested Loops]"
        elif max_loop_depth >= 3:
            time_complexity = f"O(n^{max_loop_depth}) [Polynomial/High Complexity]"
        else:
            time_complexity = "O(n)"

        # Estimate Space Complexity
        has_collections = any(isinstance(n, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp)) for n in ast.walk(tree))
        if has_collections or recursive_calls:
            space_complexity = "O(n) [Linear Space]"
        else:
            space_complexity = "O(1) [Auxiliary In-Place Space]"

        # Scoring heuristics
        quality = 90.0
        suggestions: list[str] = []

        if max_loop_depth >= 2:
            quality -= 15.0
            suggestions.append("Consider replacing nested loops with a hash map or two-pointer approach to optimize from O(n^2) to O(n).")

        if branch_count > 8:
            quality -= 10.0
            suggestions.append("Cyclomatic complexity is elevated (>8 branches). Modularize helper logic into discrete functions.")

        if loc > 100:
            quality -= 5.0
            suggestions.append("Solution is lengthy (>100 LOC). Check for redundancy or over-engineering.")

        if recursive_calls and not any(isinstance(n, ast.If) for n in ast.walk(tree)):
            quality -= 20.0
            suggestions.append("Potential infinite recursion detected: ensure clear base cases exist.")

        quality = max(20.0, min(100.0, quality))

        return StaticAnalysisMetrics(
            estimated_time_complexity=time_complexity,
            estimated_space_complexity=space_complexity,
            cyclomatic_complexity=branch_count,
            lines_of_code=loc,
            loop_depth=max_loop_depth,
            has_recursion=recursive_calls,
            quality_score=quality,
            suggestions=suggestions,
        )


class IsolatedCodeSandbox:
    """Enterprise-grade code execution sandbox running candidate code in an isolated subprocess."""

    HARNESS_TEMPLATE = '''
import json
import sys
import time
import traceback

{candidate_code}

test_cases = {test_cases_json}
results = []

for idx, tc in enumerate(test_cases):
    is_public = tc.get("is_public", True)
    inp = tc.get("input")
    expected = tc.get("expected_output")
    fn_name = tc.get("entry_point") or "solution"

    # Locate target function
    fn = globals().get(fn_name)
    if fn is None:
        # Fallback: look for the first callable defined in candidate code
        callables = [v for k, v in globals().items() if callable(v) and not k.startswith("_") and k != "run_tests"]
        if callables:
            fn = callables[0]

    if fn is None:
        results.append({{
            "test_index": idx,
            "is_public": is_public,
            "passed": False,
            "input_repr": str(inp),
            "expected_repr": str(expected),
            "actual_repr": None,
            "execution_time_ms": 0.0,
            "error": f"Function '{{fn_name}}' not found in submission.",
            "stdout": ""
        }})
        continue

    # Capture stdout during test run
    start_time = time.perf_counter()
    try:
        # Determine invocation format
        if isinstance(inp, dict):
            actual = fn(**inp)
        elif isinstance(inp, (list, tuple)):
            actual = fn(*inp)
        elif inp is None:
            actual = fn()
        else:
            actual = fn(inp)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Check equality (with float tolerance if numbers)
        passed = False
        if isinstance(expected, float) and isinstance(actual, (int, float)):
            passed = abs(expected - actual) < 1e-5
        else:
            passed = (actual == expected)

        results.append({{
            "test_index": idx,
            "is_public": is_public,
            "passed": passed,
            "input_repr": repr(inp),
            "expected_repr": repr(expected),
            "actual_repr": repr(actual),
            "execution_time_ms": elapsed_ms,
            "error": None if passed else f"Assertion failed: expected {{expected!r}}, got {{actual!r}}",
            "stdout": ""
        }})
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        results.append({{
            "test_index": idx,
            "is_public": is_public,
            "passed": False,
            "input_repr": repr(inp),
            "expected_repr": repr(expected),
            "actual_repr": None,
            "execution_time_ms": elapsed_ms,
            "error": f"{{type(exc).__name__}}: {{exc}}",
            "stdout": ""
        }})

print("__SANDBOX_RESULTS_START__")
print(json.dumps(results))
print("__SANDBOX_RESULTS_END__")
'''

    def __init__(self, default_timeout_s: float = 3.0) -> None:
        self.default_timeout_s = default_timeout_s
        self.security_validator = CodeSecurityValidator()
        self.ast_analyzer = CodeASTComplexityAnalyzer()

    async def execute(
        self,
        code: str,
        test_cases: list[dict[str, Any]],
        language: str = "python",
        timeout_s: float | None = None,
        entry_point: str | None = None,
    ) -> SandboxExecutionResult:
        """Execute candidate code against test cases with safety, timeouts, and metrics."""
        effective_timeout = timeout_s or self.default_timeout_s
        start_wall = time.perf_counter()

        # 1. Static AST Analysis & Security Policy Enforcement
        static_metrics = self.ast_analyzer.analyze(code)

        if language.lower() in ("python", "py"):
            try:
                tree = ast.parse(code)
                validator = CodeSecurityValidator()
                validator.visit(tree)
                if validator.violations:
                    return SandboxExecutionResult(
                        success=False,
                        total_tests=len(test_cases),
                        passed_tests=0,
                        failed_tests=len(test_cases),
                        pass_rate=0.0,
                        total_execution_time_ms=0.0,
                        test_results=[],
                        static_analysis=static_metrics,
                        security_passed=False,
                        error=f"Security Policy Violation: {'; '.join(validator.violations)}",
                    )
            except SyntaxError as err:
                return SandboxExecutionResult(
                    success=False,
                    total_tests=len(test_cases),
                    passed_tests=0,
                    failed_tests=len(test_cases),
                    pass_rate=0.0,
                    total_execution_time_ms=0.0,
                    test_results=[],
                    static_analysis=static_metrics,
                    security_passed=False,
                    error=f"SyntaxError: {err.msg} at line {err.lineno}",
                )

        # Ensure entry_point is attached to test cases if specified
        normalized_tests: list[dict[str, Any]] = []
        for tc in test_cases:
            t_copy = dict(tc)
            if entry_point and "entry_point" not in t_copy:
                t_copy["entry_point"] = entry_point
            normalized_tests.append(t_copy)

        # 2. Build isolated runner script in temp directory
        harness_code = self.HARNESS_TEMPLATE.format(
            candidate_code=code,
            test_cases_json=repr(normalized_tests),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "submission_runner.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(harness_code)

            # 3. Spawn isolated subprocess with timeout
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir,
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=effective_timeout,
                    )
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                        await proc.communicate()
                    except Exception:
                        pass
                    total_wall = (time.perf_counter() - start_wall) * 1000.0
                    return SandboxExecutionResult(
                        success=False,
                        total_tests=len(test_cases),
                        passed_tests=0,
                        failed_tests=len(test_cases),
                        pass_rate=0.0,
                        total_execution_time_ms=total_wall,
                        test_results=[
                            TestCaseResult(
                                test_index=i,
                                is_public=tc.get("is_public", True),
                                passed=False,
                                input_repr=str(tc.get("input")),
                                expected_repr=str(tc.get("expected_output")),
                                actual_repr=None,
                                execution_time_ms=effective_timeout * 1000.0,
                                error="TimeLimitExceeded: execution exceeded time limit (infinite loop or high complexity)",
                            )
                            for i, tc in enumerate(test_cases)
                        ],
                        static_analysis=static_metrics,
                        security_passed=True,
                        error=f"TimeLimitExceeded: Code execution exceeded {effective_timeout}s time limit.",
                    )

            except Exception as proc_exc:
                log.error("sandbox_proc_failed", error=str(proc_exc))
                return SandboxExecutionResult(
                    success=False,
                    total_tests=len(test_cases),
                    passed_tests=0,
                    failed_tests=len(test_cases),
                    pass_rate=0.0,
                    total_execution_time_ms=(time.perf_counter() - start_wall) * 1000.0,
                    test_results=[],
                    static_analysis=static_metrics,
                    security_passed=True,
                    error=f"Execution process error: {proc_exc}",
                )

        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stderr_text = stderr_bytes.decode("utf-8", errors="replace")
        total_time_ms = (time.perf_counter() - start_wall) * 1000.0

        # Parse test results delimiter
        start_tag = "__SANDBOX_RESULTS_START__"
        end_tag = "__SANDBOX_RESULTS_END__"

        if start_tag in stdout_text and end_tag in stdout_text:
            raw_json = stdout_text.split(start_tag)[1].split(end_tag)[0].strip()
            try:
                parsed_runs = json.loads(raw_json)
                test_case_results: list[TestCaseResult] = []
                passed_count = 0

                for item in parsed_runs:
                    p = bool(item.get("passed", False))
                    if p:
                        passed_count += 1
                    test_case_results.append(TestCaseResult(
                        test_index=item.get("test_index", 0),
                        is_public=item.get("is_public", True),
                        passed=p,
                        input_repr=item.get("input_repr", ""),
                        expected_repr=item.get("expected_repr", ""),
                        actual_repr=item.get("actual_repr"),
                        execution_time_ms=float(item.get("execution_time_ms", 0.0)),
                        error=item.get("error"),
                        stdout=item.get("stdout", ""),
                    ))

                total_cases = len(test_case_results)
                pass_rate = (passed_count / total_cases) if total_cases > 0 else 0.0

                return SandboxExecutionResult(
                    success=(passed_count == total_cases),
                    total_tests=total_cases,
                    passed_tests=passed_count,
                    failed_tests=total_cases - passed_count,
                    pass_rate=pass_rate,
                    total_execution_time_ms=total_time_ms,
                    test_results=test_case_results,
                    static_analysis=static_metrics,
                    security_passed=True,
                    error=None if passed_count == total_cases else f"{total_cases - passed_count} test(s) failed.",
                )
            except Exception as json_err:
                log.error("sandbox_json_parse_err", error=str(json_err), raw=raw_json)

        # If harness failed to output valid JSON (e.g. fatal runtime crash)
        err_msg = stderr_text.strip() or stdout_text.strip() or "Program crashed unexpectedly during execution."
        return SandboxExecutionResult(
            success=False,
            total_tests=len(test_cases),
            passed_tests=0,
            failed_tests=len(test_cases),
            pass_rate=0.0,
            total_execution_time_ms=total_time_ms,
            test_results=[
                TestCaseResult(
                    test_index=i,
                    is_public=tc.get("is_public", True),
                    passed=False,
                    input_repr=str(tc.get("input")),
                    expected_repr=str(tc.get("expected_output")),
                    actual_repr=None,
                    execution_time_ms=0.0,
                    error=err_msg[:300],
                )
                for i, tc in enumerate(test_cases)
            ],
            static_analysis=static_metrics,
            security_passed=True,
            error=err_msg[:400],
        )
