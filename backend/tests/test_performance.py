"""
Tests for Interview Performance Analytics and Placement Readiness APIs (Module 11).
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def mock_ollama_provider():
    """Autouse fixture to prevent real Ollama network timeouts during tests."""
    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ConnectionError("Ollama offline in test sandbox")
        yield mock_gen


@pytest.mark.asyncio
async def test_get_performance_empty_state(client: AsyncClient, auth_headers: dict[str, str]):
    """Test performance analytics endpoint when user has 0 interviews."""
    res = await client.get("/api/v1/performance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_interviews"] == 0
    assert data["average_score"] is None
    assert data["has_enough_data"] is False
    assert data["score_history"] == []


@pytest.mark.asyncio
async def test_get_readiness_empty_state(client: AsyncClient, auth_headers: dict[str, str]):
    """Test placement readiness endpoint when user has no mock interviews or resume analysis."""
    res = await client.get("/api/v1/readiness", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Sample user has basic profile skills so 1 component is available
    assert data["available_metrics_count"] >= 1
    assert data["overall_readiness_score"] is not None
    assert len(data["breakdown"]) == 4
    assert len(data["recommendations"]) > 0



@pytest.mark.asyncio
async def test_get_performance_and_readiness_with_completed_interviews(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test performance stats and readiness calculation after completing mock interviews."""
    # Create and evaluate mock interview session 1
    create_res1 = await client.post(
        "/api/v1/interviews",
        json={"role": "Software Engineer", "difficulty": "Easy", "total_questions": 1},
        headers=auth_headers,
    )
    s1 = create_res1.json()["data"]
    q1_id = s1["current_question"]["id"]

    eval1_json = """
    {
      "technical_correctness": 70.0,
      "relevance": 70.0,
      "completeness": 70.0,
      "communication": 70.0,
      "structure": 70.0,
      "clarity": 70.0,
      "overall_score": 70.0,
      "feedback": "Solid basic response.",
      "strengths": ["Basic concepts"],
      "improvements": ["More depth"],
      "ideal_answer": "Sample ideal answer."
    }
    """

    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = eval1_json
        await client.post(
            f"/api/v1/interviews/{s1['id']}/answer",
            json={"question_id": q1_id, "user_answer": "Candidate answer 1."},
            headers=auth_headers,
        )

    # Create and evaluate mock interview session 2 (higher score)
    create_res2 = await client.post(
        "/api/v1/interviews",
        json={"role": "Software Engineer", "difficulty": "Medium", "total_questions": 1},
        headers=auth_headers,
    )
    s2 = create_res2.json()["data"]
    q2_id = s2["current_question"]["id"]

    eval2_json = """
    {
      "technical_correctness": 90.0,
      "relevance": 90.0,
      "completeness": 90.0,
      "communication": 90.0,
      "structure": 90.0,
      "clarity": 90.0,
      "overall_score": 90.0,
      "feedback": "Outstanding response.",
      "strengths": ["Deep expertise"],
      "improvements": ["None"],
      "ideal_answer": "Sample ideal answer 2."
    }
    """

    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = eval2_json
        await client.post(
            f"/api/v1/interviews/{s2['id']}/answer",
            json={"question_id": q2_id, "user_answer": "Candidate answer 2."},
            headers=auth_headers,
        )

    # 1. Verify GET /api/v1/performance
    perf_res = await client.get("/api/v1/performance", headers=auth_headers)
    assert perf_res.status_code == 200
    perf_data = perf_res.json()["data"]

    assert perf_data["total_interviews"] == 2
    assert perf_data["average_score"] == 80.0
    assert perf_data["best_score"] == 90.0
    assert perf_data["latest_score"] == 90.0
    assert perf_data["improvement"] == 20.0  # 90.0 - 70.0 = +20.0
    assert len(perf_data["score_history"]) == 2
    assert perf_data["score_history"][0]["score"] == 70.0
    assert perf_data["score_history"][1]["score"] == 90.0

    # 2. Verify GET /api/v1/readiness
    read_res = await client.get("/api/v1/readiness", headers=auth_headers)
    assert read_res.status_code == 200
    read_data = read_res.json()["data"]

    assert read_data["overall_readiness_score"] is not None
    assert read_data["available_metrics_count"] >= 1
    assert read_data["level"] in ["Job Ready", "Nearly Ready", "Needs Preparation"]

    # 3. Verify GET /api/v1/dashboard includes real interview & readiness stats
    dash_res = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["interviews"]["total_mock_interviews"] == 2
    assert dash_data["interviews"]["average_score"] == 80.0
    assert dash_data["placement_readiness"]["readiness_score"] is not None
