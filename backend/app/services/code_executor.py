"""
Secure Sandbox Code Execution Engine (Module 12).
Executes candidate code safely outside the FastAPI process using isolated subprocesses and in-memory SQLite instances.
"""

import ast
import json
import logging
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

logger = logging.getLogger(__name__)

# Execution security limits
MAX_EXECUTION_TIME_SECONDS = 3.0
MAX_OUTPUT_BYTES = 10000


class CodeExecutionResult:
    """Standard container for a single test case execution result."""

    def __init__(
        self,
        test_case_index: int,
        input_data: str,
        expected_output: str,
        passed: bool,
        actual_output: str | None = None,
        error_output: str | None = None,
        execution_time_ms: float = 0.0,
    ):
        self.test_case_index = test_case_index
        self.input_data = input_data
        self.expected_output = expected_output
        self.passed = passed
        self.actual_output = actual_output
        self.error_output = error_output
        self.execution_time_ms = round(execution_time_ms, 2)

    def to_dict(self) -> dict:
        return {
            "test_case_index": self.test_case_index,
            "input_data": self.input_data,
            "expected_output": self.expected_output,
            "passed": self.passed,
            "actual_output": self.actual_output,
            "error_output": self.error_output,
            "execution_time_ms": self.execution_time_ms,
        }


def execute_python_code_in_sandbox(
    candidate_code: str,
    test_cases: list[dict],
) -> tuple[str, int, int, float, list[CodeExecutionResult]]:
    """Execute Python/DSA candidate code in an isolated subprocess sandbox.

    Args:
        candidate_code: Python source code submitted by user.
        test_cases: List of test case objects with 'input' and 'expected_output'.

    Returns:
        tuple: (overall_status, passed_count, total_count, total_time_ms, results_list)
    """
    # Quick static syntax check before spawning subprocess
    try:
        ast.parse(candidate_code)
    except SyntaxError as syn_err:
        results = []
        for idx, tc in enumerate(test_cases):
            results.append(
                CodeExecutionResult(
                    test_case_index=idx,
                    input_data=tc.get("input", ""),
                    expected_output=tc.get("expected_output", ""),
                    passed=False,
                    error_output=f"Syntax Error: {syn_err.msg} at line {syn_err.lineno}",
                )
            )
        return "Syntax Error", 0, len(test_cases), 0.0, results

    results: list[CodeExecutionResult] = []
    passed_count = 0
    total_time_ms = 0.0
    overall_status = "Passed"

    for idx, tc in enumerate(test_cases):
        input_str = tc.get("input", "")
        expected_out = str(tc.get("expected_output", "")).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "solution.py")

            # Wrapper code to parse inputs, invoke function, and print output
            runner_wrapper = f"""# Isolated Sandbox Script
import json
import sys

{candidate_code}

# Test invocation harness
if __name__ == '__main__':
    try:
        # Parse inputs from harness
        raw_input = \"\"\"{input_str}\"\"\"
        lines = [line.strip() for line in raw_input.strip().split('\\n') if line.strip()]
        
        # Call available defined entry point functions in solution scope
        funcs = [v for k, v in list(globals().items()) if callable(v) and not k.startswith('_') and k != 'json']
        if not funcs:
            print("No function definition found.", file=sys.stderr)
            sys.exit(1)
        
        target_fn = funcs[-1]
        
        # Evaluate arguments from lines
        args = []
        for line in lines:
            if '=' in line:
                val_part = line.split('=', 1)[1].strip()
            else:
                val_part = line.strip()
            try:
                args.append(eval(val_part, {{"__builtins__": None}}, {{}}))
            except Exception:
                args.append(val_part)
                
        res = target_fn(*args)
        if isinstance(res, (dict, list)):
            print(json.dumps(res))
        else:
            print(str(res))
    except Exception as exc:
        print(f"Runtime Exception: {{exc}}", file=sys.stderr)
        sys.exit(1)
"""
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(runner_wrapper)

            start_time = time.perf_counter()
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-S", script_path],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=MAX_EXECUTION_TIME_SECONDS,
                )
                exec_ms = (time.perf_counter() - start_time) * 1000
                total_time_ms += exec_ms

                actual_out = proc.stdout.strip()
                err_out = proc.stderr.strip()

                if proc.returncode != 0:
                    status = "Failed"
                    if overall_status == "Passed":
                        overall_status = "Runtime Error"
                    passed = False
                else:
                    # Normalize JSON / text string comparison
                    passed = False
                    try:
                        parsed_actual = json.loads(actual_out)
                        parsed_expected = json.loads(expected_out)
                        passed = (parsed_actual == parsed_expected)
                    except Exception:
                        passed = (actual_out.lower() == expected_out.lower())

                    if passed:
                        passed_count += 1

                results.append(
                    CodeExecutionResult(
                        test_case_index=idx,
                        input_data=input_str,
                        expected_output=expected_out,
                        passed=passed,
                        actual_output=actual_out if actual_out else None,
                        error_output=err_out if err_out else None,
                        execution_time_ms=exec_ms,
                    )
                )

            except subprocess.TimeoutExpired:
                exec_ms = MAX_EXECUTION_TIME_SECONDS * 1000
                total_time_ms += exec_ms
                if overall_status == "Passed":
                    overall_status = "Time Limit Exceeded"
                results.append(
                    CodeExecutionResult(
                        test_case_index=idx,
                        input_data=input_str,
                        expected_output=expected_out,
                        passed=False,
                        error_output=f"Execution timed out (> {MAX_EXECUTION_TIME_SECONDS}s).",
                        execution_time_ms=exec_ms,
                    )
                )

    if passed_count < len(test_cases) and overall_status == "Passed":
        overall_status = "Failed"

    return overall_status, passed_count, len(test_cases), round(total_time_ms, 2), results


def execute_sql_code_in_sandbox(
    candidate_sql: str,
    sql_schema: str | None,
    test_cases: list[dict],
) -> tuple[str, int, int, float, list[CodeExecutionResult]]:
    """Execute SQL candidate query safely against an in-memory SQLite database.

    Args:
        candidate_sql: SQL query string submitted by user.
        sql_schema: Table schema DDL and dataset insertion DML.
        test_cases: List of expected output test cases.

    Returns:
        tuple: (overall_status, passed_count, total_count, total_time_ms, results_list)
    """
    results: list[CodeExecutionResult] = []
    passed_count = 0
    total_time_ms = 0.0
    overall_status = "Passed"

    for idx, tc in enumerate(test_cases):
        input_str = tc.get("input", "SQL Dataset Query")
        expected_out = str(tc.get("expected_output", "")).strip()

        start_time = time.perf_counter()
        conn = None
        try:
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()

            # Initialize schema & data
            if sql_schema and sql_schema.strip():
                cursor.executescript(sql_schema)

            # Execute candidate query
            cursor.execute(candidate_sql)
            rows = cursor.fetchall()
            exec_ms = (time.perf_counter() - start_time) * 1000
            total_time_ms += exec_ms

            actual_json = json.dumps([list(row) for row in rows])

            passed = False
            try:
                parsed_actual = json.loads(actual_json)
                parsed_expected = json.loads(expected_out)
                passed = (parsed_actual == parsed_expected)
            except Exception:
                passed = (actual_json.strip() == expected_out.strip())

            if passed:
                passed_count += 1

            results.append(
                CodeExecutionResult(
                    test_case_index=idx,
                    input_data=input_str,
                    expected_output=expected_out,
                    passed=passed,
                    actual_output=actual_json,
                    error_output=None,
                    execution_time_ms=exec_ms,
                )
            )
        except Exception as sql_err:
            exec_ms = (time.perf_counter() - start_time) * 1000
            total_time_ms += exec_ms
            if overall_status == "Passed":
                overall_status = "Syntax Error" if "syntax" in str(sql_err).lower() else "Runtime Error"

            results.append(
                CodeExecutionResult(
                    test_case_index=idx,
                    input_data=input_str,
                    expected_output=expected_out,
                    passed=False,
                    error_output=f"SQL Execution Error: {sql_err}",
                    execution_time_ms=exec_ms,
                )
            )
        finally:
            if conn:
                conn.close()

    if passed_count < len(test_cases) and overall_status == "Passed":
        overall_status = "Failed"

    return overall_status, passed_count, len(test_cases), round(total_time_ms, 2), results


def execute_code_safely(
    language: str,
    candidate_code: str,
    test_cases: list[dict],
    sql_schema: str | None = None,
) -> tuple[str, int, int, float, list[CodeExecutionResult]]:
    """Polymorphic entry point for safe code sandbox execution."""
    if language.lower() == "sql":
        return execute_sql_code_in_sandbox(candidate_code, sql_schema, test_cases)
    else:
        return execute_python_code_in_sandbox(candidate_code, test_cases)
