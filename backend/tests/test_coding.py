"""
Tests for Coding Challenge System & Secure Sandbox Execution (Module 12).
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def mock_ollama_provider():
    """Autouse fixture to prevent real Ollama network timeouts during tests."""
    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = '{"hint": "Use two pointers", "explanation": "Move left and right pointers towards center."}'
        yield mock_gen


@pytest.mark.asyncio
async def test_list_coding_challenges(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/coding/challenges returns standard seeded challenges."""
    res = await client.get("/api/v1/coding/challenges", headers=auth_headers)
    assert res.status_code == 200
    challenges = res.json()["data"]
    assert len(challenges) >= 3

    # Filter by category
    res_dsa = await client.get("/api/v1/coding/challenges?category=DSA", headers=auth_headers)
    assert res_dsa.status_code == 200
    dsa_challenges = res_dsa.json()["data"]
    assert all(c["category"] == "DSA" for c in dsa_challenges)


@pytest.mark.asyncio
async def test_get_coding_challenge_detail(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/coding/challenges/two-sum returns problem detail and starter code."""
    res = await client.get("/api/v1/coding/challenges/two-sum", headers=auth_headers)
    assert res.status_code == 200
    ch = res.json()["data"]
    assert ch["title"] == "Two Sum"
    assert ch["slug"] == "two-sum"
    assert "def two_sum" in ch["starter_code"]


@pytest.mark.asyncio
async def test_submit_python_challenge_success(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/coding/challenges/{id}/submit executes Python solution in sandbox."""
    ch_res = await client.get("/api/v1/coding/challenges/two-sum", headers=auth_headers)
    ch_id = ch_res.json()["data"]["id"]

    valid_solution = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
"""

    sub_res = await client.post(
        f"/api/v1/coding/challenges/{ch_id}/submit",
        json={"code": valid_solution, "language": "python"},
        headers=auth_headers,
    )
    assert sub_res.status_code == 200
    sub = sub_res.json()["data"]

    assert sub["status"] == "Passed"
    assert sub["passed_test_cases"] == sub["total_test_cases"]
    assert len(sub["results"]) >= 2
    assert all(r["passed"] is True for r in sub["results"])


@pytest.mark.asyncio
async def test_submit_sql_challenge_success(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/coding/challenges/{id}/submit executes SQL solution in SQLite sandbox."""
    ch_res = await client.get("/api/v1/coding/challenges/department-highest-salary", headers=auth_headers)
    ch_id = ch_res.json()["data"]["id"]

    valid_sql = """
SELECT Department.name AS Department, Employee.name AS Employee, Employee.salary AS Salary
FROM Employee
JOIN Department ON Employee.department_id = Department.id
WHERE (Employee.department_id, Employee.salary) IN (
    SELECT department_id, MAX(salary)
    FROM Employee
    GROUP BY department_id
)
ORDER BY Department.name ASC, Employee.name ASC
"""

    sub_res = await client.post(
        f"/api/v1/coding/challenges/{ch_id}/submit",
        json={"code": valid_sql, "language": "sql"},
        headers=auth_headers,
    )
    assert sub_res.status_code == 200
    sub = sub_res.json()["data"]

    assert sub["status"] == "Passed"
    assert sub["passed_test_cases"] == sub["total_test_cases"]


@pytest.mark.asyncio
async def test_submit_code_with_syntax_error(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/coding/challenges/{id}/submit returns Syntax Error status for invalid code."""
    ch_res = await client.get("/api/v1/coding/challenges/two-sum", headers=auth_headers)
    ch_id = ch_res.json()["data"]["id"]

    invalid_code = "def two_sum(nums, target) return [0, 1]"  # missing colon

    sub_res = await client.post(
        f"/api/v1/coding/challenges/{ch_id}/submit",
        json={"code": invalid_code, "language": "python"},
        headers=auth_headers,
    )
    assert sub_res.status_code == 200
    sub = sub_res.json()["data"]

    assert sub["status"] == "Syntax Error"
    assert sub["passed_test_cases"] == 0


@pytest.mark.asyncio
async def test_get_submissions_history(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/coding/challenges/{id}/submissions returns history of candidate submissions."""
    ch_res = await client.get("/api/v1/coding/challenges/two-sum", headers=auth_headers)
    ch_id = ch_res.json()["data"]["id"]

    # Submit solution
    await client.post(
        f"/api/v1/coding/challenges/{ch_id}/submit",
        json={"code": "def two_sum(n, t): return [0, 1]", "language": "python"},
        headers=auth_headers,
    )

    history_res = await client.get(f"/api/v1/coding/challenges/{ch_id}/submissions", headers=auth_headers)
    assert history_res.status_code == 200
    submissions = history_res.json()["data"]

    assert len(submissions) >= 1
    assert submissions[0]["challenge_id"] == ch_id


@pytest.mark.asyncio
async def test_get_ai_coding_hint(client: AsyncClient, auth_headers: dict[str, str]):
    """POST /api/v1/coding/challenges/{id}/hint returns Ollama AI hints."""
    ch_res = await client.get("/api/v1/coding/challenges/two-sum", headers=auth_headers)
    ch_id = ch_res.json()["data"]["id"]

    hint_res = await client.post(
        f"/api/v1/coding/challenges/{ch_id}/hint",
        json={"code": "def two_sum(n, t): pass", "language": "python"},
        headers=auth_headers,
    )
    assert hint_res.status_code == 200
    hint_data = hint_res.json()["data"]

    assert "hint" in hint_data
    assert "explanation" in hint_data
