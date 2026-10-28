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

# Strict whitelist of permitted algorithm / standard library modules
ALLOWED_MODULES = {
    "math",
    "collections",
    "itertools",
    "heapq",
    "bisect",
    "string",
    "typing",
    "functools",
    "re",
    "random",
    "json",
    "datetime",
}

# Explicitly forbidden function and builtin calls that could bypass sandbox or access system
FORBIDDEN_CALLS = {
    "open",
    "compile",
    "eval",
    "exec",
    "__import__",
    "globals",
    "locals",
    "vars",
    "input",
    "breakpoint",
    "exit",
    "quit",
    "help",
    "getattr",
    "setattr",
    "delattr",
}

# Forbidden dunder attributes used for reflection / sandbox escape
FORBIDDEN_ATTRIBUTES = {
    "__subclasses__",
    "__bases__",
    "__globals__",
    "__code__",
    "__closure__",
    "__builtins__",
    "__import__",
    "__loader__",
    "__spec__",
    "__dict__",
    "__class__",
    "__mro__",
}

# Forbidden SQL tokens that could inspect disk or attach external databases
FORBIDDEN_SQL_KEYWORDS = {
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "LOAD_EXTENSION",
    "ALTER SYSTEM",
}


class SecurityViolationError(Exception):
    """Raised when submitted code contains prohibited constructs or modules."""
    pass


class ASTSecurityValidator(ast.NodeVisitor):
    """Inspects candidate AST before execution to prevent RCE, OS access, and sandbox escapes."""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_module = alias.name.split(".")[0]
            if root_module not in ALLOWED_MODULES:
                raise SecurityViolationError(
                    f"Importing module '{alias.name}' is prohibited in the execution sandbox."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root_module = node.module.split(".")[0]
            if root_module not in ALLOWED_MODULES:
                raise SecurityViolationError(
                    f"Importing from module '{node.module}' is prohibited in the execution sandbox."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            raise SecurityViolationError(
                f"Calling '{node.func.id}()' is prohibited in the execution sandbox."
            )
        elif isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_CALLS:
            raise SecurityViolationError(
                f"Calling method '{node.func.attr}()' is prohibited in the execution sandbox."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in FORBIDDEN_ATTRIBUTES:
            raise SecurityViolationError(
                f"Accessing restricted attribute '{node.attr}' is prohibited in the execution sandbox."
            )
        self.generic_visit(node)


def validate_candidate_code_security(code: str) -> None:
    """Perform AST static security analysis to ensure code cannot perform malicious actions.
    
    Raises:
        SyntaxError: If code cannot be parsed.
        SecurityViolationError: If code attempts forbidden operations.
    """
    tree = ast.parse(code)
    validator = ASTSecurityValidator()
    validator.visit(tree)


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
    # 1. Static security & syntax check before spawning subprocess
    try:
        validate_candidate_code_security(candidate_code)
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
    except SecurityViolationError as sec_err:
        results = []
        for idx, tc in enumerate(test_cases):
            results.append(
                CodeExecutionResult(
                    test_case_index=idx,
                    input_data=tc.get("input", ""),
                    expected_output=tc.get("expected_output", ""),
                    passed=False,
                    error_output=f"Security Violation: {sec_err}",
                )
            )
        return "Security Violation", 0, len(test_cases), 0.0, results

    results: list[CodeExecutionResult] = []
    passed_count = 0
    total_time_ms = 0.0
    overall_status = "Passed"

    for idx, tc in enumerate(test_cases):
        input_str = tc.get("input", "")
        expected_out = str(tc.get("expected_output", "")).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "solution.py")

            # Safely encode the test input string as a JSON string literal
            encoded_input_json = json.dumps(input_str)

            # Wrapper code to parse inputs safely, invoke function, and print output
            runner_wrapper = f"""# Isolated Sandbox Script
import ast
import json
import sys

# Candidate code submitted by user
{candidate_code}

# Test invocation harness
if __name__ == '__main__':
    try:
        raw_input = {encoded_input_json}
        lines = [line.strip() for line in raw_input.strip().split('\\n') if line.strip()]
        
        # Locate candidate entry point function
        funcs = [
            v for k, v in list(globals().items())
            if callable(v) and not k.startswith('_') and k not in ('json', 'ast', 'sys')
        ]
        if not funcs:
            print("No function definition found.", file=sys.stderr)
            sys.exit(1)
        
        target_fn = funcs[-1]
        
        # Parse arguments safely using literal_eval (no arbitrary eval)
        args = []
        for line in lines:
            if '=' in line:
                val_part = line.split('=', 1)[1].strip()
            else:
                val_part = line.strip()
            try:
                args.append(ast.literal_eval(val_part))
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
    # Security check on candidate SQL statement
    upper_sql = candidate_sql.upper()
    for kw in FORBIDDEN_SQL_KEYWORDS:
        if kw in upper_sql:
            sec_res = [
                CodeExecutionResult(
                    test_case_index=idx,
                    input_data=tc.get("input", "SQL Dataset Query"),
                    expected_output=str(tc.get("expected_output", "")).strip(),
                    passed=False,
                    error_output=f"Security Violation: SQL command '{kw}' is not permitted in sandbox.",
                )
                for idx, tc in enumerate(test_cases)
            ]
            return "Security Violation", 0, len(test_cases), 0.0, sec_res

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
